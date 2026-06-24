# Causal-Direction Tables Glossary

Short guide to the technical labels used in the causal-direction tables.

## Model Names

- `populism_to_corruption`: tests whether past governing populism predicts later/current corruption.
- `corruption_to_populism`: tests whether past corruption predicts later/current governing populism.
- `lead_lag`: fixed-effects model using lagged values of the proposed cause.
- `granger`: stricter model including both the dependent variable's own lags and the proposed cause's lags.
- `placebo`: model adding future values of the proposed cause as a pre-trend/placebo check.
- `event_study`: model comparing years before/after a defined event.
- `_controlled`: model includes `log_gdppc` and `v2x_polyarchy`.
- `_no_controls`: model excludes those controls.

## Lag And Lead Labels

- `L1`: one lag, `t-1`.
- `L2`: two lags, `t-1` and `t-2`.
- `L3`: three lags, `t-1`, `t-2`, `t-3`.
- `F1`: one future lead, `t+1`.
- `F2`: two future leads, `t+1` and `t+2`.
- `L2_F2`: two past lags and two future leads.
- `lag_order`: number of past years included in the model.
- `coef_lag1`: coefficient for the one-year lag.
- `coef_lag2`: coefficient for the two-year lag.

## Controls

- `log_gdppc`: log GDP per capita, used as an economic-development control.
- `v2x_polyarchy`: electoral democracy, used as a democracy/institutional control.
- `controls = log_gdppc, v2x_polyarchy`: model includes both controls.
- `controls = none`: model does not include them.

## Fixed Effects

- `country_fe = True`: country fixed effects are included.
- `year_fe = True`: year fixed effects are included.
- Country fixed effects remove stable differences between countries.
- Year fixed effects remove common shocks/trends affecting all countries in a given year.

## Granger-Style Tables

- `dependent_variable`: outcome being predicted.
- `proposed_cause`: variable whose past values are tested as predictors.
- `joint_test_p`: p-value for the joint test that all proposed-cause lags equal zero. (joint = Wald chi-square test)
- `joint_df`: degrees of freedom in the joint test.
- `do not reject H0`: the proposed-cause lags do not add clear predictive information.
- `reject H0`: the proposed-cause lags are jointly significant.

## Placebo Lead Tables

- `term_type = lag`: past value of the proposed cause.
- `term_type = lead_placebo`: future value of the proposed cause.
- `lead_joint_p`: joint p-value for the future placebo leads.
- `placebo_warning = True`: future values are jointly significant; possible pre-trend/anticipation issue.
- `placebo_warning = False`: no strong placebo-lead warning.

## Event-Study Tables

- `event_time`: year relative to the event.
- `event_m3`: three years before the event, `t-3`.
- `event_m2`: two years before the event, `t-2`.
- `reference`: omitted baseline year, here usually `t-1`.
- `event_p0`: event year, `t`.
- `event_p1`: one year after the event, `t+1`.
- `event_p2`: two years after the event, `t+2`.
- `pretrend_joint_p`: joint test for pre-event coefficients.
- `post_joint_p`: joint test for event/post-event coefficients.
- `n_events`: number of events identified.
- `event_definition`: rule used to define the event.

## Electoral Sample Robustness

- `all`: full estimation sample.
- `election_years`: only country-years marked as election years.
- `government_change_years`: only years where `populism_governing` changes.
- `ffill_le5`: observations at most 5 years after the last election.
- `ffill_le10`: observations at most 10 years after the last election.
- These checks test whether results depend on forward-filled government-populism values.

## First Differences

- `delta_v2x_corr`: annual change in corruption.
- `delta_populism_governing`: annual change in governing populism.
- `cause_delta_lag`: lagged annual change in the proposed cause.
- First-difference models ask whether a previous change predicts a current change.

## Information Criteria

- `aic`: Akaike Information Criterion; lower is better.
- `bic`: Bayesian Information Criterion; lower is better and penalizes complexity more strongly.
- `best_aic = True`: lowest AIC among tested lag orders.
- `best_bic = True`: lowest BIC among tested lag orders.

## Democracy Heterogeneity

- `democracy_interaction`: model allowing the populism lag effect to vary by `v2x_polyarchy`.
- `democracy_split`: model estimated separately for lower- and higher-democracy country groups.
- `low_p10`, `median_p50`, `high_p90`: marginal effects evaluated at the 10th, 50th, and 90th percentiles of democracy.
- `low_democracy_countries`: countries at or below the median country-average `v2x_polyarchy`.
- `high_democracy_countries`: countries above the median country-average `v2x_polyarchy`.
