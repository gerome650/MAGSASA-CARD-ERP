package resilience

import data.resilience.deny

# Use set comprehensions + count() to avoid unsafe wildcard variables.

test_deny_on_chaos_failure {
  input := {"chaos_failed": true, "slo_regressions": 0}
  count({m | deny[m] with input as input}) > 0
}

test_deny_on_slo_regressions {
  input := {"chaos_failed": false, "slo_regressions": 2}
  count({m | deny[m] with input as input}) > 0
}

test_allow_when_clean {
  input := {"chaos_failed": false, "slo_regressions": 0}
  count({m | deny[m] with input as input}) == 0
}
