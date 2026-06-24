**Table 4 — Lead-lag and Granger-style joint Wald tests**

| outcome_key | outcome | direction | model | sample_mode | joint_statistic | joint_p_value | joint_df | within_r2 | n_obs | n_countries | country_fe | year_fe | clustered_by_country | fdr_q_value | reject_fdr_05 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| composite | Composite | populism_to_corruption | lead_lag | outcome_specific | 4.6398 | 0.0983 | 2 | -0.1834 | 3750 | 95 | True | True | True | — | False |
| composite | Composite | populism_to_corruption | granger | outcome_specific | 0.7532 | 0.6862 | 2 | 0.8862 | 3750 | 95 | True | True | True | — | False |
| composite | Composite | corruption_to_populism | lead_lag | outcome_specific | 5.9809 | 0.0503 | 2 | -0.0066 | 3750 | 95 | True | True | True | — | False |
| composite | Composite | corruption_to_populism | granger | outcome_specific | 2.8483 | 0.2407 | 2 | 0.6985 | 3750 | 95 | True | True | True | — | False |
| executive | Executive | populism_to_corruption | lead_lag | outcome_specific | 0.3033 | 0.8593 | 2 | -0.0790 | 3750 | 95 | True | True | True | 0.8593 | False |
| executive | Executive | populism_to_corruption | granger | outcome_specific | 1.4031 | 0.4958 | 2 | 0.8569 | 3750 | 95 | True | True | True | 0.6611 | False |
| executive | Executive | corruption_to_populism | lead_lag | outcome_specific | 1.6204 | 0.4448 | 2 | -0.0012 | 3750 | 95 | True | True | True | 0.5083 | False |
| executive | Executive | corruption_to_populism | granger | outcome_specific | 0.2792 | 0.8697 | 2 | 0.6985 | 3750 | 95 | True | True | True | 0.8697 | False |
| public_sector | Public sector | populism_to_corruption | lead_lag | outcome_specific | 3.7455 | 0.1537 | 2 | -0.2097 | 3750 | 95 | True | True | True | 0.2333 | False |
| public_sector | Public sector | populism_to_corruption | granger | outcome_specific | 0.6178 | 0.7343 | 2 | 0.8733 | 3750 | 95 | True | True | True | 0.8392 | False |
| public_sector | Public sector | corruption_to_populism | lead_lag | outcome_specific | 5.0421 | 0.0804 | 2 | -0.0081 | 3750 | 95 | True | True | True | 0.1607 | False |
| public_sector | Public sector | corruption_to_populism | granger | outcome_specific | 2.9683 | 0.2267 | 2 | 0.6985 | 3750 | 95 | True | True | True | 0.5023 | False |
| legislative | Legislative | populism_to_corruption | lead_lag | outcome_specific | 8.0466 | 0.0179 | 2 | -0.1382 | 3576 | 95 | True | True | True | 0.0477 | True |
| legislative | Legislative | populism_to_corruption | granger | outcome_specific | 11.3148 | 0.0035 | 2 | 0.8704 | 3501 | 95 | True | True | True | 0.0279 | True |
| legislative | Legislative | corruption_to_populism | lead_lag | outcome_specific | 3.4866 | 0.1749 | 2 | 0.0023 | 3527 | 95 | True | True | True | 0.2333 | False |
| legislative | Legislative | corruption_to_populism | granger | outcome_specific | 5.4930 | 0.0642 | 2 | 0.6942 | 3527 | 95 | True | True | True | 0.2566 | False |
| judicial | Judicial | populism_to_corruption | lead_lag | outcome_specific | 8.7989 | 0.0123 | 2 | -0.0425 | 3750 | 95 | True | True | True | 0.0477 | True |
| judicial | Judicial | populism_to_corruption | granger | outcome_specific | 2.3035 | 0.3161 | 2 | 0.8667 | 3750 | 95 | True | True | True | 0.5057 | False |
| judicial | Judicial | corruption_to_populism | lead_lag | outcome_specific | 9.8210 | 0.0074 | 2 | 0.0131 | 3750 | 95 | True | True | True | 0.0477 | True |
| judicial | Judicial | corruption_to_populism | granger | outcome_specific | 2.7634 | 0.2512 | 2 | 0.6987 | 3750 | 95 | True | True | True | 0.5023 | False |
| composite | Composite | populism_to_corruption | lead_lag | common | 4.5723 | 0.1017 | 2 | -0.1604 | 3576 | 95 | True | True | True | — | False |
| composite | Composite | populism_to_corruption | granger | common | 1.5177 | 0.4682 | 2 | 0.8997 | 3501 | 95 | True | True | True | — | False |
| composite | Composite | corruption_to_populism | lead_lag | common | 5.2324 | 0.0731 | 2 | -0.0001 | 3527 | 95 | True | True | True | — | False |
| composite | Composite | corruption_to_populism | granger | common | 4.5998 | 0.1003 | 2 | 0.6940 | 3527 | 95 | True | True | True | — | False |
| executive | Executive | populism_to_corruption | lead_lag | common | 0.3591 | 0.8357 | 2 | -0.0631 | 3576 | 95 | True | True | True | 0.8357 | False |
| executive | Executive | populism_to_corruption | granger | common | 1.4259 | 0.4902 | 2 | 0.8581 | 3501 | 95 | True | True | True | 0.6536 | False |
| executive | Executive | corruption_to_populism | lead_lag | common | 1.2671 | 0.5307 | 2 | 0.0050 | 3527 | 95 | True | True | True | 0.6065 | False |
| executive | Executive | corruption_to_populism | granger | common | 0.5362 | 0.7648 | 2 | 0.6939 | 3527 | 95 | True | True | True | 0.7648 | False |
| public_sector | Public sector | populism_to_corruption | lead_lag | common | 3.8773 | 0.1439 | 2 | -0.1724 | 3576 | 95 | True | True | True | 0.2302 | False |
| public_sector | Public sector | populism_to_corruption | granger | common | 1.5062 | 0.4709 | 2 | 0.8774 | 3501 | 95 | True | True | True | 0.6536 | False |
| public_sector | Public sector | corruption_to_populism | lead_lag | common | 4.8624 | 0.0879 | 2 | -0.0000 | 3527 | 95 | True | True | True | 0.1759 | False |
| public_sector | Public sector | corruption_to_populism | granger | common | 2.9086 | 0.2336 | 2 | 0.6939 | 3527 | 95 | True | True | True | 0.4671 | False |
| legislative | Legislative | populism_to_corruption | lead_lag | common | 8.0466 | 0.0179 | 2 | -0.1382 | 3576 | 95 | True | True | True | 0.0947 | False |
| legislative | Legislative | populism_to_corruption | granger | common | 11.3148 | 0.0035 | 2 | 0.8704 | 3501 | 95 | True | True | True | 0.0279 | True |
| legislative | Legislative | corruption_to_populism | lead_lag | common | 3.4866 | 0.1749 | 2 | 0.0023 | 3527 | 95 | True | True | True | 0.2333 | False |
| legislative | Legislative | corruption_to_populism | granger | common | 5.4930 | 0.0642 | 2 | 0.6942 | 3527 | 95 | True | True | True | 0.2566 | False |
| judicial | Judicial | populism_to_corruption | lead_lag | common | 6.0790 | 0.0479 | 2 | -0.0110 | 3576 | 95 | True | True | True | 0.1276 | False |
| judicial | Judicial | populism_to_corruption | granger | common | 1.0131 | 0.6026 | 2 | 0.8737 | 3501 | 95 | True | True | True | 0.6887 | False |
| judicial | Judicial | corruption_to_populism | lead_lag | common | 7.4867 | 0.0237 | 2 | 0.0148 | 3527 | 95 | True | True | True | 0.0947 | False |
| judicial | Judicial | corruption_to_populism | granger | common | 2.9092 | 0.2335 | 2 | 0.6942 | 3527 | 95 | True | True | True | 0.4671 | False |
