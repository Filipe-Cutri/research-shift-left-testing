# Technical Smoke Test — Lang-1

**Date:** 2026-11-25  
**Project:** Apache Commons Lang  
**Defect:** Lang-1 (LANG-747)  
**Purpose:** Validate the execution environment and the integration of Defects4J, PMD, and SpotBugs.

## 1. Environment validation

The following operations were completed successfully:

- Checked out the buggy version (`Lang-1b`).
- Checked out the fixed version (`Lang-1f`).
- Compiled both versions successfully using Defects4J.
- Executed the reference test on both versions.
- Executed PMD 7.19.0 on both versions.
- Executed SpotBugs 4.10.5 on both versions.

## 2. Reference test results

| Version | Result |
|---|---|
| Lang-1b (buggy) | 1 failing test |
| Lang-1f (fixed) | 0 failing tests |

The triggering test was:

`org.apache.commons.lang3.math.NumberUtilsTest::TestLang747`

The failure involved a `NumberFormatException` when processing the hexadecimal value `80000000`.

## 3. Static analysis results

| Tool | Buggy version | Fixed version |
|---|---:|---:|
| PMD 7.19.0 | 513 violations | 513 violations |
| SpotBugs 4.10.5 | 275 findings | 275 findings |

The comparison of individual findings showed:

- PMD: 488 findings in common; two findings disappeared and two appeared at shifted line positions.
- SpotBugs: 271 findings in common; three findings disappeared and three appeared at different line positions.

The changed findings were not demonstrated to be related to the defect's corrective code.

## 4. Defect correction

The fix modified `org.apache.commons.lang3.math.NumberUtils`.

The change added handling for leading zeroes in hexadecimal numbers and additional checks for values exceeding the signed `int` and `long` ranges. Values exceeding those limits are routed to larger numeric types.

No PMD or SpotBugs finding was identified as directly detecting this behavioral defect.

## 5. Technical conclusion

The smoke test confirmed that:

- Defects4J can retrieve, compile, and test both versions.
- The reference test distinguishes the buggy and fixed versions.
- PMD and SpotBugs execute successfully on the selected project.
- The total number of static analysis findings remained unchanged between versions.
- No direct detection of LANG-747 by either static analyzer was established.

This result is a technical validation only. Lang-1 is not treated as a pilot sample or as evidence for the final experimental conclusions.

## 6. Limitations

The findings from this single defect cannot be generalized to the complete Defects4J population.

The final experiment will evaluate all eligible defects from Apache Commons Lang, Jsoup, and Gson, applying the predefined selection criteria.
