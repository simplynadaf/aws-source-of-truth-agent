import {defineField, defineType} from 'sanity'

/**
 * awsFact: one atomic, current AWS fact (a quota, limit, price, version support,
 * or regional availability) as a typed document. This is the STRUCTURED half of
 * the challenge angle: the agent can filter on real fields (service, region,
 * factType) instead of fuzzy-matching prose.
 *
 * Each fact records the source it came from and the "current" value, plus any
 * superseded value it replaced, so the KB build has an explicit contradiction to
 * reconcile and cite.
 */
export const awsFact = defineType({
  name: 'awsFact',
  title: 'AWS Fact',
  type: 'document',
  fields: [
    defineField({
      name: 'service',
      title: 'Service',
      type: 'string',
      description: 'e.g. EC2, Lambda, S3, RDS',
      validation: (r) => r.required(),
    }),
    defineField({
      name: 'factType',
      title: 'Fact type',
      type: 'string',
      options: {
        list: ['quota', 'limit', 'price', 'versionSupport', 'regionalAvailability'],
      },
      validation: (r) => r.required(),
    }),
    defineField({
      name: 'key',
      title: 'Fact key',
      type: 'string',
      description: 'The thing being measured, e.g. "Running On-Demand Standard vCPUs"',
      validation: (r) => r.required(),
    }),
    defineField({
      name: 'currentValue',
      title: 'Current value',
      type: 'string',
      description: 'The value that is true right now, e.g. "5" or "$0.023 per GB-month"',
      validation: (r) => r.required(),
    }),
    defineField({
      name: 'unit',
      title: 'Unit',
      type: 'string',
      description: 'e.g. vCPUs, GB-month, requests/sec',
    }),
    defineField({
      name: 'region',
      title: 'Region',
      type: 'string',
      description: 'AWS region code, or "global". e.g. us-east-1',
    }),
    defineField({
      name: 'effectiveDate',
      title: 'Effective date',
      type: 'date',
      description: 'When this value became current. Used to pick the winner when sources disagree.',
    }),
    defineField({
      name: 'source',
      title: 'Source',
      type: 'object',
      fields: [
        {name: 'name', title: 'Source name', type: 'string'},
        {name: 'url', title: 'Source URL', type: 'url'},
        {
          name: 'kind',
          title: 'Source kind',
          type: 'string',
          options: {list: ['officialDocs', 'pricingPage', 'serviceQuotasConsole', 'changelog', 'blog']},
        },
      ],
      validation: (r) => r.required(),
    }),
    defineField({
      name: 'supersedes',
      title: 'Supersedes (the value this replaced)',
      type: 'object',
      description:
        'If a source still shows an older value, record it here so the reconciliation is explicit and citable.',
      fields: [
        {name: 'value', title: 'Old value', type: 'string'},
        {name: 'stillShownBy', title: 'Still shown by (source name)', type: 'string'},
        {name: 'stillShownUrl', title: 'Still shown by (URL)', type: 'url'},
        {name: 'reason', title: 'Why current wins', type: 'string'},
      ],
    }),
    defineField({
      name: 'notes',
      title: 'Notes',
      type: 'text',
    }),
  ],
  preview: {
    select: {title: 'key', subtitle: 'service', value: 'currentValue'},
    prepare({title, subtitle, value}) {
      return {title: `${title} = ${value}`, subtitle}
    },
  },
})
