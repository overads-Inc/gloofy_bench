# gloofy taxonomy rules

**Version 2.0**, effective 17 Aug 2026.

These rules are the contract between the training data, the model and
the exams. They changed once without being recorded, which caused the
exam drift documented in EVAL-CARD-r14.md. From now on every change
bumps this version, and every exam states which version keyed it.

## Facets and closed vocabulary

- **hook**: question, bold_claim, statistic, problem_callout,
  curiosity_gap, social_proof, direct_offer, story_open, none_evident
- **angle**: pain_relief, aspiration, authority, novelty, price_value,
  urgency, comparison, community, none_evident
- **persona**: consumer_general, parent, professional, business_owner,
  developer, student, enthusiast, none_evident
- **offer**: discount, free_trial, free_shipping, bundle,
  gift_with_purchase, lead_magnet, demo_or_consult, none_evident
- **funnel_stage**: awareness, consideration, decision, retention,
  none_evident

## Rules, with the version each was introduced

### v1.0, from the first human review
1. **persona is the economic role the ad sells to**, never an incidental
   identity inside a story. An ad telling a parent's story to sell a work
   tool targets professional.
2. **business_owner runs the business; professional is an employed
   individual** buying for their own work.
3. **Numeric evidence claims are statistic**, not social_proof.
   social_proof is peer-adoption framing ("join 12,000 developers").
4. **A permanent free tier is offer none_evident.** free_trial must be
   time-limited.
5. **funnel_stage decision requires purchase mechanics in the ad
   itself**: a price, a buy or enrol CTA, or a redeemable offer.
   Evaluation content (demo, study, comparison, walkthrough) is
   consideration however commanding the CTA verb sounds.

### v2.0, from measuring the model against real published ads
6. **Length is not evidence.** A four-word ad can carry a claim; a
   forty-word ad can carry none. Judge what is asserted, never how much
   text there is.
7. **A claim asserted in four words is still bold_claim.** It does not
   need a supporting argument to count.
8. **Emoji, hashtags and ALL CAPS are formatting, not signals.** Read
   past them to the proposition.
9. **Brand-mood copy gets none_evident on hook**, but rarely on
   funnel_stage. A lookbook or seasonal ad that asserts nothing is
   hook none_evident, angle novelty or aspiration where a mood is
   evoked, and funnel_stage awareness or consideration according to
   whether it points at a specific product. **funnel_stage none_evident
   is reserved for ads that give no directional signal at all**, which
   is rare in real advertising.
10. **direct_offer means the ad IS the deal.** A confident tone is not
    an offer.

Rule 9 is the one that caused the drift. Exam v2.0's ambiguous stratum
was keyed under an implicit reading where mood ads took none_evident on
several facets at once. Real annotators applying rules 6 through 10 do
not label that way, so that stratum is being re-keyed as v2.1 with the
original preserved.

## How a rule changes

1. Propose it with the measurement that motivated it.
2. Bump this file's version.
3. Re-key affected exam strata by three-annotator consensus.
4. Publish the old and new keys side by side, never replacing.
