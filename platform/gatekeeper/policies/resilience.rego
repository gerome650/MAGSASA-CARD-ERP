package resilience

# 'deny' is a SET of strings. Each rule may add entries.

# Deny if any chaos scenarios failed
deny[msg] {
  input.chaos_failed == true
  msg := "Chaos failures detected"
}

# Deny if SLO regressions present
deny[msg] {
  input.slo_regressions > 0
  msg := sprintf("%v SLO regression(s) detected", [input.slo_regressions])
}
