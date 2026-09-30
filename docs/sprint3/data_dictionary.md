# Sprint 3 data dictionary

Fields retain Sprint 1/2 meanings; new derived fields are marked. Nullable reflects the accepted artifact.

| file | field_name | definition | source | unit | raw_or_derived | nullable | analysis_role |
|---|---|---|---|---|---|---|---|
| offensive_recognition_features.csv | pitch_key | pitch key | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | game_pk | game pk | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | game_date | game date | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | recognized | recognized | derived by Sprint 3 | count | derived | no | outcome |
| offensive_recognition_features.csv | survival_class | survival class | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | challenge_outcome | challenge outcome | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | yes | audit/output |
| offensive_recognition_features.csv | challenged | challenged | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | distance_from_abs_boundary | distance from abs boundary | retained Sprint 1/2 pitch/challenge field | feet | retained | no | audit/output |
| offensive_recognition_features.csv | abs_distance | abs distance | derived by Sprint 3 | feet | derived | no | predictor |
| offensive_recognition_features.csv | abs_distance_inches | abs distance inches | derived by Sprint 3 | inches | derived | no | audit/output |
| offensive_recognition_features.csv | miss_axis | miss axis | derived by Sprint 3 | identifier/text | derived | no | predictor |
| offensive_recognition_features.csv | miss_side | miss side | derived by Sprint 3 | identifier/text | derived | no | predictor |
| offensive_recognition_features.csv | horizontal_distance | horizontal distance | derived by Sprint 3 | feet | derived | no | predictor |
| offensive_recognition_features.csv | horizontal_distance_inches | horizontal distance inches | derived by Sprint 3 | inches | derived | no | audit/output |
| offensive_recognition_features.csv | vertical_distance | vertical distance | derived by Sprint 3 | feet | derived | no | predictor |
| offensive_recognition_features.csv | vertical_distance_inches | vertical distance inches | derived by Sprint 3 | inches | derived | no | audit/output |
| offensive_recognition_features.csv | corner_proximity | corner proximity | derived by Sprint 3 | identifier/text | derived | no | predictor |
| offensive_recognition_features.csv | corner_proximity_inches | corner proximity inches | derived by Sprint 3 | inches | derived | no | audit/output |
| offensive_recognition_features.csv | plate_x | plate x | retained Sprint 1/2 pitch/challenge field | feet | retained | no | audit/output |
| offensive_recognition_features.csv | plate_z | plate z | retained Sprint 1/2 pitch/challenge field | feet | retained | no | audit/output |
| offensive_recognition_features.csv | abs_zone_top | abs zone top | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | abs_zone_bot | abs zone bot | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | pitch_type | pitch type | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | pitch_family | pitch family | derived by Sprint 3 | identifier/text | derived | no | predictor |
| offensive_recognition_features.csv | release_speed | release speed | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| offensive_recognition_features.csv | release_spin_rate | release spin rate | retained Sprint 1/2 pitch/challenge field | probability | retained | yes | predictor |
| offensive_recognition_features.csv | spin_axis | spin axis | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | yes | audit/output |
| offensive_recognition_features.csv | spin_axis_sin | spin axis sin | derived by Sprint 3 | identifier/text | derived | yes | predictor |
| offensive_recognition_features.csv | spin_axis_cos | spin axis cos | derived by Sprint 3 | identifier/text | derived | yes | predictor |
| offensive_recognition_features.csv | pfx_x | pfx x | retained Sprint 1/2 pitch/challenge field | feet | retained | no | predictor |
| offensive_recognition_features.csv | pfx_z | pfx z | retained Sprint 1/2 pitch/challenge field | feet | retained | no | predictor |
| offensive_recognition_features.csv | extension | extension | retained Sprint 1/2 pitch/challenge field | feet | retained | yes | predictor |
| offensive_recognition_features.csv | release_pos_x | release pos x | retained Sprint 1/2 pitch/challenge field | feet | retained | no | predictor |
| offensive_recognition_features.csv | release_pos_z | release pos z | retained Sprint 1/2 pitch/challenge field | feet | retained | no | predictor |
| offensive_recognition_features.csv | pitch_hand | pitch hand | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| offensive_recognition_features.csv | bat_side | bat side | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| offensive_recognition_features.csv | inning | inning | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| offensive_recognition_features.csv | balls | balls | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | strikes | strikes | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | count | count | derived by Sprint 3 | identifier/text | derived | no | predictor |
| offensive_recognition_features.csv | outs | outs | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| offensive_recognition_features.csv | on_1b | on 1b | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | yes | audit/output |
| offensive_recognition_features.csv | on_2b | on 2b | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | yes | audit/output |
| offensive_recognition_features.csv | on_3b | on 3b | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | yes | audit/output |
| offensive_recognition_features.csv | base_state | base state | derived by Sprint 3 | identifier/text | derived | no | predictor |
| offensive_recognition_features.csv | score_diff | score diff | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | offense_score_diff | offense score diff | derived by Sprint 3 | identifier/text | derived | no | predictor |
| offensive_recognition_features.csv | affected_team_challenges_remaining | affected team challenges remaining | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| offensive_recognition_features.csv | strike_three_call | strike three call | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_features.csv | inning_group | inning group | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_features.csv | score_state | score state | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_features.csv | batter_id | batter id | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| offensive_recognition_features.csv | batter_name | batter name | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | pitcher_id | pitcher id | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| offensive_recognition_features.csv | pitcher_name | pitcher name | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | catcher_id | catcher id | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| offensive_recognition_features.csv | catcher_name | catcher name | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | umpire_id | umpire id | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| offensive_recognition_features.csv | umpire_name | umpire name | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_features.csv | month | month | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_features.csv | date_scope | date scope | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_features.csv | feature_version | feature version | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_predictions.csv | pitch_key | pitch key | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_predictions.csv | game_pk | game pk | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_predictions.csv | game_date | game date | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_predictions.csv | fold | fold | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_predictions.csv | model | model | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_predictions.csv | recognized | recognized | derived by Sprint 3 | count | derived | no | outcome |
| offensive_recognition_predictions.csv | predicted_probability | predicted probability | derived by Sprint 3 | probability | derived | no | audit/output |
| offensive_recognition_model_metrics.csv | model | model | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_model_metrics.csv | n | n | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_model_metrics.csv | recognized | recognized | derived by Sprint 3 | count | derived | no | outcome |
| offensive_recognition_model_metrics.csv | not_recognized | not recognized | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| offensive_recognition_model_metrics.csv | validation | validation | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_model_metrics.csv | regularization | regularization | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_model_metrics.csv | roc_auc | roc auc | derived by Sprint 3 | probability | derived | no | audit/output |
| offensive_recognition_model_metrics.csv | pr_auc | pr auc | derived by Sprint 3 | probability | derived | no | audit/output |
| offensive_recognition_model_metrics.csv | log_loss | log loss | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_model_metrics.csv | brier_score | brier score | derived by Sprint 3 | probability | derived | no | audit/output |
| offensive_recognition_model_metrics.csv | calibration_intercept | calibration intercept | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_model_metrics.csv | calibration_slope | calibration slope | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| offensive_recognition_model_metrics.csv | ece_10bin | ece 10bin | derived by Sprint 3 | probability | derived | no | audit/output |
| identity_effects.csv | entity_type | entity type | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| identity_effects.csv | entity_id | entity id | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | predictor |
| identity_effects.csv | entity_name | entity name | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| identity_effects.csv | opportunities | opportunities | retained Sprint 1/2 pitch/challenge field | count | retained | no | audit/output |
| identity_effects.csv | recognized | recognized | derived by Sprint 3 | count | derived | no | outcome |
| identity_effects.csv | raw_recognition_rate | raw recognition rate | derived by Sprint 3 | probability | derived | no | audit/output |
| identity_effects.csv | expected_recognized | expected recognized | derived by Sprint 3 | count | derived | no | audit/output |
| identity_effects.csv | expected_recognition_rate | expected recognition rate | derived by Sprint 3 | probability | derived | no | audit/output |
| identity_effects.csv | adjusted_recognition_rate | adjusted recognition rate | derived by Sprint 3 | probability | derived | no | audit/output |
| identity_effects.csv | adjusted_effect | adjusted effect | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| identity_effects.csv | ci95_low | ci95 low | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| identity_effects.csv | ci95_high | ci95 high | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| identity_effects.csv | support_eligible | support eligible | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| identity_effects.csv | rank_eligible | rank eligible | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| identity_effects.csv | identity_model_supported | identity model supported | derived by Sprint 3 | identifier/text | derived | no | audit/output |
| identity_effects.csv | method | method | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| model_comparisons.csv | transition | transition | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| model_comparisons.csv | baseline_model | baseline model | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| model_comparisons.csv | expanded_model | expanded model | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| model_comparisons.csv | delta_roc_auc | delta roc auc | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| model_comparisons.csv | delta_pr_auc | delta pr auc | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| model_comparisons.csv | delta_log_loss | delta log loss | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
| model_comparisons.csv | delta_brier_score | delta brier score | retained Sprint 1/2 pitch/challenge field | identifier/text | retained | no | audit/output |
