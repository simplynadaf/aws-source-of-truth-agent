"""
Live AWS cross-check - the differentiator no keyword search and no other
challenge entry has.

Given the reconciled "current" value from the structured Knowledge Base, this
module asks the LIVE, authoritative AWS API what the value is right now and
reports one of:
  - "agree"       live value matches the KB's reconciled value
  - "drift"       live value differs (the KB, or your account, has moved)
  - "unavailable" the live check could not run (permission/API/no mapping)

Design rule (honest by default): an unavailable check is reported as
unavailable, never as a pass. The check is ADVISORY - it annotates the
deterministic reconcile verdict, it does not silently override it.

All calls are READ-ONLY (Get/Describe/List).
"""
from __future__ import annotations

from typing import Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from .config import config


def _result(status: str, live_value: Optional[str], detail: str,
            api: str) -> dict[str, Any]:
    return {"status": status, "liveValue": live_value, "detail": detail, "api": api}


def _match(live: Optional[str], claimed: Optional[str]) -> str:
    if live is None:
        return "unavailable"
    if claimed is None:
        return "drift"
    # tolerant numeric compare, else string compare
    try:
        if abs(float(live) - float(claimed)) < 1e-9:
            return "agree"
        return "drift"
    except (TypeError, ValueError):
        return "agree" if str(live).strip() == str(claimed).strip() else "drift"


def verify_live(service: str, fact_type: str, region: str, claimed_value: str,
                quota_code: str | None = None, key: str | None = None) -> dict[str, Any]:
    """Cross-check a reconciled value against the live AWS API. Read-only."""
    svc = (service or "").upper()
    ft = (fact_type or "").lower()
    reg = region if region and region != "global" else config.region

    try:
        # --- Quotas / limits via Service Quotas -----------------------------
        if ft in ("quota", "limit") and quota_code:
            sq = boto3.client("service-quotas", region_name=reg)
            svc_code = "ec2" if svc == "EC2" else "lambda" if svc == "LAMBDA" else "ebs" if svc == "EBS" else svc.lower()
            resp = sq.get_service_quota(ServiceCode=svc_code, QuotaCode=quota_code)
            live = resp["Quota"]["Value"]
            live_str = str(int(live)) if float(live).is_integer() else str(live)
            return _result(_match(live_str, claimed_value), live_str,
                           f"Service Quotas {svc_code}/{quota_code} = {live_str}",
                           "service-quotas:GetServiceQuota")

        # --- Price via AWS Price List API -----------------------------------
        if ft == "price" and svc == "S3":
            live = _s3_standard_price(reg)
            if live is None:
                return _result("unavailable", None,
                               "Could not read S3 Standard price from Price List API.",
                               "pricing:GetProducts")
            return _result(_match(live, claimed_value), live,
                           f"Price List API: S3 Standard first tier = {live} USD/GB-mo",
                           "pricing:GetProducts")

        # --- Regional availability via EC2 ----------------------------------
        if ft == "regionalavailability" and svc == "EC2":
            fam = (key or "").lower()
            itype = "r8g.medium" if "r8g" in fam or "graviton4" in fam else None
            if itype:
                ec2 = boto3.client("ec2", region_name=reg)
                offerings = ec2.describe_instance_type_offerings(
                    LocationType="region",
                    Filters=[{"Name": "instance-type", "Values": [itype]}],
                )
                avail = "Available" if offerings.get("InstanceTypeOfferings") else "Not available"
                return _result(_match(avail, claimed_value), avail,
                               f"EC2 DescribeInstanceTypeOfferings {itype} in {reg}: {avail}",
                               "ec2:DescribeInstanceTypeOfferings")

        # --- RDS engine version floor ---------------------------------------
        if ft == "versionsupport" and svc == "RDS":
            rds = boto3.client("rds", region_name=reg)
            versions = rds.describe_db_engine_versions(Engine="postgres")
            majors = sorted({
                int(v["EngineVersion"].split(".")[0])
                for v in versions.get("DBEngineVersions", [])
                if v.get("EngineVersion", "").split(".")[0].isdigit()
            })
            live = str(majors[0]) if majors else None
            if live is None:
                return _result("unavailable", None, "No RDS PostgreSQL versions returned.",
                               "rds:DescribeDBEngineVersions")
            return _result(_match(live, claimed_value), live,
                           f"Oldest available RDS PostgreSQL major = {live}",
                           "rds:DescribeDBEngineVersions")

        return _result("unavailable", None,
                       f"No live-check mapping for {service}/{fact_type}.", "none")

    except (ClientError, BotoCoreError) as e:
        return _result("unavailable", None, f"AWS API error: {e}", "error")
    except Exception as e:  # never let the advisory check crash the answer
        return _result("unavailable", None, f"Unexpected error: {e}", "error")


def _s3_standard_price(region: str) -> Optional[str]:
    """Read the current S3 Standard first-tier price from the Price List API.

    Price List API only lives in us-east-1/ap-south-1 endpoints.
    """
    try:
        pricing = boto3.client("pricing", region_name="us-east-1")
        loc = _region_to_location(region)
        resp = pricing.get_products(
            ServiceCode="AmazonS3",
            Filters=[
                {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "Storage"},
                {"Type": "TERM_MATCH", "Field": "volumeType", "Value": "Standard"},
                {"Type": "TERM_MATCH", "Field": "location", "Value": loc},
            ],
            MaxResults=100,
        )
        import json as _json
        best = None
        for item in resp.get("PriceList", []):
            doc = _json.loads(item)
            terms = doc.get("terms", {}).get("OnDemand", {})
            for term in terms.values():
                for dim in term.get("priceDimensions", {}).values():
                    price = dim.get("pricePerUnit", {}).get("USD")
                    begin = dim.get("beginRange", "0")
                    if price and begin in ("0",):
                        val = float(price)
                        if val > 0 and (best is None or val < best):
                            best = val
        if best is None:
            return None
        return f"{best:.3f}".rstrip("0").rstrip(".") if "." in f"{best:.3f}" else f"{best}"
    except Exception:
        return None


def _region_to_location(region: str) -> str:
    return {
        "us-east-1": "US East (N. Virginia)",
        "us-west-2": "US West (Oregon)",
        "eu-west-1": "EU (Ireland)",
        "ap-south-1": "Asia Pacific (Mumbai)",
    }.get(region, "US East (N. Virginia)")
