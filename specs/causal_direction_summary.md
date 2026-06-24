# Causal direction: bidirectional summary

Full explanation: `docs/explanation/causal_direction_explained.md`.

## Question

The task tests both directions:

- `corruption -> populism`: is higher corruption followed by higher governing populism?
- `populism -> corruption`: is governing populism followed by higher overall political corruption?

All models use country fixed effects, year fixed effects, and the controls `log_gdppc` and
`v2x_polyarchy`.

## Corruption -> Populism

The lead-lag model does not find clear corruption-lag coefficients. The stricter Granger-style test
also does not reject the null (`p = 0.241` in the two-lag model). The placebo lead test does not flag
future-corruption leads (`p = 0.841`). The corruption-shock event-study shows a post-event signal,
but governing populism is already elevated before the shock, so this should be read as contextual
clustering around the same episodes rather than clean causal evidence. First differences are null.

Conclusion: no robust evidence that corruption is followed by higher governing populism.

## Populism -> Corruption

The simple two-lag lead-lag model has a negative lag-1 coefficient (`coef = -0.048`, `p = 0.031`),
not the hypothesised positive sign. The stricter Granger-style test does not reject the null
(`p = 0.686`). The placebo lead test does not flag future-populism leads (`p = 0.096`). The
populist-entry event-study shows no pre-trend and no clear post-entry corruption increase. First
differences are null.

Conclusion: no robust evidence that governing populism is followed by higher overall corruption.

The lag-window comparison uses AIC/BIC only as approximate diagnostics with shrinking samples. Longer
lag windows drop additional early country-years, so the criteria help describe the fitted models but
should not be treated as definitive lag-selection evidence.

## Report Sentence

The bidirectional panel analysis does not provide robust evidence for either temporal direction:
higher corruption is not clearly followed by higher governing populism, and governing populism is not
clearly followed by higher overall political corruption once persistence, controls, and fixed effects
are accounted for.
