# Grades (blind, from key and trap only)

| ID | Q | Grade | EXTRA | Reason |
|---|---|---|---|---|
| ans-01 | 1 | CORRECT | Y | Score 85 live, foreign archived, other disqualifiers draft; 'unless the link is also broken' not in key |
| ans-01 | 2 | CORRECT | Y | 'given unless the job is explicitly marked as having a failing apply link' |
| ans-01 | 3 | CORRECT | Y | Title 1.5 vs department 0.5 weighting; department counts only for unmatched tier |
| ans-01 | 4 | CORRECT | Y | 'takes them from the board's own fields where it has them', title keywords otherwise |
| ans-01 | 5 | CORRECT | Y | 'covers only the Gemini AI reader'; fresh reader per company, pause not carried over |
| ans-01 | 6 | CORRECT | Y | '429 or RESOURCE_EXHAUSTED' rotates key; 'Timeouts and other errors do not cause a switch' |
| ans-01 | 7 | CORRECT | Y | 'a request where every free key fails would use four free keys and stop without touching the paid one' |
| ans-01 | 8 | CORRECT | Y | Contains match over name, tags, city, sector; 'The description is not searched' |
| ans-01 | 9 | CORRECT | Y | Banner only after auto-fill finds a draft company with that domain |
| ans-01 | 10 | WRONG | Y | Exempts markdown, text, docs/, .memory, images; key lists only .github, .claude, .agents, LICENSE, .gitignore, .gitattributes, symlinks, submodules |
| ans-01 | 11 | CORRECT | Y | 'flags only when, across all changed test files together, more assertion lines were removed than added' |
| ans-01 | 12 | CORRECT | Y | 'a max-warnings limit or codecov threshold being raised' flagged; 'tightening is silent' |
| ans-01 | 13 | CORRECT | Y | 'any different version, even a lower one, passes'; x.y.z form only |
| ans-01 | 14 | CORRECT | Y | Version and timestamp lines ignored; 'generated' block 'at' line 'is not ignored and counts' |
| ans-02 | 1 | CORRECT | Y | 85 with no disqualifier goes live; 'archived only when foreign location is its top-ranked problem' |
| ans-02 | 2 | CORRECT | Y | 'unless the "link works" flag is explicitly false, so an unset flag still earns them' |
| ans-02 | 3 | CORRECT | Y | Title 15 vs department 5 per tier; department 'only for a tier when the title did not already match' |
| ans-02 | 4 | INCOMPLETE | Y | Lists title, location and fields together; no fields-first, title-fallback precedence for connectors stated |
| ans-02 | 5 | CORRECT | Y | 'covers only the company being processed'; fresh extractor per company |
| ans-02 | 6 | CORRECT | Y | 'quota error (HTTP 429 or resource exhausted)' rotates key; other failures do not switch |
| ans-02 | 7 | CORRECT | Y | 'at most 4 attempts' would use four free keys and not reach the paid key |
| ans-02 | 8 | CORRECT | Y | Contains match over name, tags, city, sector label; description not searched |
| ans-02 | 9 | CORRECT | Y | Banner only when auto-fill finds existing company with draft status |
| ans-02 | 10 | WRONG | Y | Exempts markdown, text, rst, docs/, .memory; beyond key's exhaustive list |
| ans-02 | 11 | CORRECT | Y | Flags when total of added minus removed assertion lines is below zero |
| ans-02 | 12 | CORRECT | Y | Lowered coverage minimum flagged; raised max-warnings or codecov threshold flagged |
| ans-02 | 13 | CORRECT | Y | Only unchanged version fails; 'any different version, even a lower one, passes' |
| ans-02 | 14 | CORRECT | Y | Timestamp ignored; generated 'at' date not ignored and counts as content |
| ans-03 | 1 | CORRECT | Y | Foreign archived when top problem; unreachable link outranks; override keeps live not in key |
| ans-03 | 2 | CORRECT | Y | '10 points are given unless the link is explicitly marked as not answering' |
| ans-03 | 3 | CORRECT | Y | 'a strong keyword is worth 15 points in the title but 5 in the department' |
| ans-03 | 4 | CORRECT | Y | 'reads the board's own field when it has one', otherwise title keywords |
| ans-03 | 5 | CORRECT | Y | 'The pause only applies to that one reader'; next company not paused |
| ans-03 | 6 | CORRECT | Y | 429 or RESOURCE_EXHAUSTED rotates key; 'Other errors, such as a timeout, do not switch keys' |
| ans-03 | 7 | CORRECT | Y | 'at most 4 tries'; five fresh free keys fail without reaching paid key |
| ans-03 | 8 | CORRECT | Y | Plain contains match over name, tags, city, sector; 'The company description is not searched' |
| ans-03 | 9 | CORRECT | Y | Banner when lookup finds draft company with same website domain |
| ans-03 | 10 | WRONG | Y | Exempts .md, .txt, .rst, docs/, .memory, images; key lists only three folders plus LICENSE/git files |
| ans-03 | 11 | CORRECT | Y | Flags when total assertion lines removed exceed added across test files |
| ans-03 | 12 | CORRECT | Y | 'lowering a coverage minimum' flagged; raising max-warnings flagged; tightening silent |
| ans-03 | 13 | CORRECT | Y | Equal version fails; 'a different version passes, even a lower one' |
| ans-03 | 14 | CORRECT | Y | Timestamp line ignored; 'at' date under generated block counts |
| ans-04 | 1 | CORRECT | Y | 'anything below 85 is a draft' with exceptions; foreign archived; unreachable-link precedence not in key |
| ans-04 | 2 | CORRECT | Y | '10 points unless ... explicitly flagged as not reachable'; nothing sets that flag false |
| ans-04 | 3 | CORRECT | Y | '15, 7.5 or 3.75' title vs '5, 2.5 or 1.25' department; department only for unmatched tier |
| ans-04 | 4 | CORRECT | Y | 'Where the board supplies its own field ... that text is tried first', title otherwise |
| ans-04 | 5 | CORRECT | Y | 'a brand-new extractor is created for every company'; pause does not reach next company |
| ans-04 | 6 | CORRECT | Y | 429 or resource exhausted triggers cooldown and retry; other errors do not switch |
| ans-04 | 7 | CORRECT | Y | 'would try 4 free keys and then give up without reaching the paid key' |
| ans-04 | 8 | CORRECT | Y | Contains match over name, tags, city, sector label; description not searched |
| ans-04 | 9 | CORRECT | Y | Banner only when company with that domain is draft; other status shows Already Registered |
| ans-04 | 10 | WRONG | Y | Exempts .md/.txt/.rst, docs/, .memory, images beyond key's three folders and LICENSE/git files |
| ans-04 | 11 | CORRECT | Y | Flags when total assertion lines removed exceed added |
| ans-04 | 12 | CORRECT | Y | 'lowering a coverage number, or raising a max-warnings or codecov threshold' flagged; tightening not |
| ans-04 | 13 | CORRECT | Y | 'only requires the version differs'; lower different version passes |
| ans-04 | 14 | CORRECT | Y | Timestamp line ignored; generated 'at' line counts as content |
| ans-05 | 1 | CORRECT | Y | '85 or more goes live, below 85 ... draft', then foreign archived and disqualifiers held as draft |
| ans-05 | 2 | CORRECT | Y | '10 points unless ... marked as known to fail (is_http_200 false)'; nothing sets false |
| ans-05 | 3 | CORRECT | Y | '15, 7.5 or 3.75' vs '5, 2.5 or 1.25'; department only for tiers title did not match |
| ans-05 | 4 | CORRECT | Y | 'reads them from the posting's own fields', otherwise keywords in title |
| ans-05 | 5 | CORRECT | Y | Pause covers only that company; 'the next company starts with no pause' |
| ans-05 | 6 | CORRECT | Y | 429 or RESOURCE_EXHAUSTED triggers 60s cooldown; timeouts do not switch |
| ans-05 | 7 | CORRECT | Y | Five fresh free keys: four tried, fails without reaching paid key |
| ans-05 | 8 | CORRECT | Y | Contains match over name, tags, city, sector; 'the description, is not searched' |
| ans-05 | 9 | CORRECT | Y | Banner only when auto-fill finds existing draft company with that domain |
| ans-05 | 10 | WRONG | Y | Exempts .md/.mdx/.txt/.rst, docs/, .memory, images beyond key list |
| ans-05 | 11 | CORRECT | Y | 'more assertion lines were removed than added across all test files' |
| ans-05 | 12 | CORRECT | Y | Lower coverage minimum and higher threshold or max-warnings flagged; tightening silent |
| ans-05 | 13 | CORRECT | Y | Only equal version fails; 'a lower one' passes |
| ans-05 | 14 | CORRECT | Y | Timestamp excluded; 'at:' under generated counts as content |
| ans-06 | 1 | CORRECT | Y | '85 or more, and none of these apply'; foreign archived; unreachable-link precedence not in key |
| ans-06 | 2 | CORRECT | Y | '10 points are given unless the link is explicitly marked as failing'; nothing sets it |
| ans-06 | 3 | CORRECT | Y | 15/7.5/3.75 title vs 5/2.5/1.25 department; department only if tier unmatched |
| ans-06 | 4 | CORRECT | Y | 'reads from its own feed fields where it has them', otherwise title keywords |
| ans-06 | 5 | CORRECT | Y | 'held inside that one extractor object'; fresh extractor per company |
| ans-06 | 6 | CORRECT | Y | 429 or RESOURCE_EXHAUSTED rotates key; other errors do not switch |
| ans-06 | 7 | CORRECT | Y | 'only if at least two free keys were already cooling'; four tries cannot reach paid key |
| ans-06 | 8 | CORRECT | Y | Contains match over name, tags, city, sector; description not searched |
| ans-06 | 9 | CORRECT | Y | Banner when draft company found; other status shows Already Registered |
| ans-06 | 10 | WRONG | Y | Exempts md/mdx/txt/rst, docs/, .memory, images beyond key's three folders |
| ans-06 | 11 | CORRECT | Y | Net loss across test files; each file losing more assertions listed |
| ans-06 | 12 | CORRECT | Y | Coverage minimum lowered flagged; threshold or max-warnings raised flagged; tightening silent |
| ans-06 | 13 | CORRECT | Y | 'version must differ not be higher'; lower different version passes |
| ans-06 | 14 | CORRECT | Y | Timestamp ignored; 'generated' at date counts |
| ans-07 | 1 | CORRECT | Y | '85 ... and none of the disqualifiers apply'; foreign archived; 'capped at 83' and unreachable-link precedence not in key |
| ans-07 | 2 | CORRECT | Y | '10 points go to a job unless its link was flagged as failing' |
| ans-07 | 3 | CORRECT | Y | 'counts one third'; 15 vs 5 weighting; department only for tier title did not match |
| ans-07 | 4 | TRAP | Y | 'They come mainly from keyword matching on the job title, plus the source's own fields'; fields not stated first |
| ans-07 | 5 | CORRECT | Y | Pause per extractor; each company gets fresh extractor; 'does not carry over' |
| ans-07 | 6 | CORRECT | Y | 429 or RESOURCE_EXHAUSTED rotates key; other errors do not switch |
| ans-07 | 7 | CORRECT | Y | 'at most 4 tries'; five fresh free keys fail without reaching paid key |
| ans-07 | 8 | CORRECT | Y | Contains match over name, tags, city, sector label; description not searched |
| ans-07 | 9 | CORRECT | Y | Banner when lookup finds draft company with that website domain |
| ans-07 | 10 | WRONG | Y | Exempts md/txt, docs/, .memory, images beyond key's three folders and LICENSE/git files |
| ans-07 | 11 | CORRECT | Y | Flags only when total assertion removals exceed additions across test files |
| ans-07 | 12 | CORRECT | Y | Lowered coverage minimum flagged; raised max-warnings flagged; tightening silent |
| ans-07 | 13 | CORRECT | Y | 'exactly the same' version fails; lower different version passes |
| ans-07 | 14 | CORRECT | Y | Timestamp ignored; 'at:' under generated block counts |
| ans-08 | 1 | CORRECT | Y | 85 with no flags goes live; location abroad archived; override and two-scan rules not in key |
| ans-08 | 2 | CORRECT | Y | '10 points unless ... explicitly marked as known to fail'; unchecked links get them |
| ans-08 | 3 | CORRECT | Y | '15 points in the title but 5 in the department'; department only for unmatched level |
| ans-08 | 4 | CORRECT | Y | 'reads from the job board's own fields where it has them'; AI answer first, then title |
| ans-08 | 5 | CORRECT | Y | 'every company gets a brand-new reader'; pause covers only that one company |
| ans-08 | 6 | CORRECT | Y | 'HTTP 429, or an error mentioning 429 or RESOURCE_EXHAUSTED' triggers switch; others do not |
| ans-08 | 7 | CORRECT | Y | 'at most 4 tries'; paid key reached only after free keys already cooling |
| ans-08 | 8 | CORRECT | Y | Contains match over name, tags, city, sector label; 'description is not searched' |
| ans-08 | 9 | CORRECT | Y | Banner when lookup finds company with that domain and draft status |
| ans-08 | 10 | WRONG | Y | Exempts .md/.txt/.rst, docs/, .memory, images beyond key's three folders |
| ans-08 | 11 | CORRECT | Y | Flags only when total assertion removals exceed additions across test files |
| ans-08 | 12 | CORRECT | Y | Lowered coverage minimum flagged; raised max-warnings or threshold flagged; tightening silent |
| ans-08 | 13 | CORRECT | Y | Only fails when version unchanged; 'a lower version' passes |
| ans-08 | 14 | CORRECT | Y | Timestamp ignored; 'at' line under generated counts |
| ans-09 | 1 | CORRECT | Y | '85 and nothing disqualifies it' goes live; foreign archived unless link unreachable (not in key) |
| ans-09 | 2 | CORRECT | Y | '10 points are given to any job whose link is not known to be broken'; nothing sets false |
| ans-09 | 3 | CORRECT | Y | 'counts one third'; 15/7.5/3.75 title vs 5/2.5/1.25 department; unmatched tier only |
| ans-09 | 4 | CORRECT | Y | 'Work mode comes from the source's workplace or location field when it has one, otherwise title' |
| ans-09 | 5 | CORRECT | Y | Pause held inside that one extractor; fresh extractor per company; does not carry over |
| ans-09 | 6 | CORRECT | Y | 429 or RESOURCE_EXHAUSTED rotates key; 'Other errors ... do not cause a switch' |
| ans-09 | 7 | CORRECT | Y | 'hits 429 on its first four free keys stops ... without reaching the paid key' |
| ans-09 | 8 | CORRECT | Y | Contains match over name, tags, city, sector label; description not listed as searched |
| ans-09 | 9 | CORRECT | Y | Banner only when auto-fill finds draft company; other status Already Registered |
| ans-09 | 10 | WRONG | Y | Exempts .md/.txt, docs/, .memory, images beyond key's three folders |
| ans-09 | 11 | CORRECT | Y | 'more assertion lines were removed than added' across test files |
| ans-09 | 12 | CORRECT | Y | Lowered coverage minimum or raised warning limit flagged; tightening silent |
| ans-09 | 13 | CORRECT | Y | 'does not require a higher number'; equal version fails, lower different passes |
| ans-09 | 14 | CORRECT | Y | Timestamp ignored; 'at:' under generated counts as content |
| ans-10 | 1 | CORRECT | Y | '85 and none of these flags'; foreign archived straight away; extra cap rules |
| ans-10 | 2 | CORRECT | Y | 'The score adds 10 points unless the job's link is explicitly flagged as not reachable' |
| ans-10 | 3 | CORRECT | Y | 'counts one third'; 15 vs 5 weighting; department only for unmatched level |
| ans-10 | 4 | CORRECT | Y | 'reads them from the hiring system's own fields where that system offers one', title otherwise |
| ans-10 | 5 | CORRECT | Y | 'pause covers only the company being processed'; fresh extractor per company |
| ans-10 | 6 | CORRECT | Y | 429 or resource exhausted triggers cooldown; other failures such as timeouts do not switch |
| ans-10 | 7 | CORRECT | Y | 'at most 4 tries'; paid key reached only after free keys already cooling |
| ans-10 | 8 | CORRECT | Y | Contains match over name, tags, city, sector; 'description is not searched' |
| ans-10 | 9 | CORRECT | Y | Banner only when company with same domain is draft |
| ans-10 | 10 | WRONG | Y | Exempts md/mdx/txt/rst, docs/, .memory, images beyond key's three folders |
| ans-10 | 11 | CORRECT | Y | Flags when total assertion removals exceed additions across test files |
| ans-10 | 12 | CORRECT | Y | Lower coverage minimum and higher max-warnings or threshold flagged; tightening silent |
| ans-10 | 13 | CORRECT | Y | 'fails only when' version unchanged; lower different version passes |
| ans-10 | 14 | CORRECT | Y | Timestamp ignored; generated 'at' date counts |
| ans-11 | 1 | CORRECT | Y | 'a broken link takes priority over foreign location'; override not in key; 85 rule correct |
| ans-11 | 2 | CORRECT | Y | '10 points given to any job whose link is not known to be broken' |
| ans-11 | 3 | CORRECT | Y | 'half' not used; 15/7.5/3.75 title vs 5/2.5/1.25 department; unmatched tier only |
| ans-11 | 4 | INCOMPLETE | Y | Title and location plus board fields listed together; no fields-first, title-fallback precedence stated |
| ans-11 | 5 | CORRECT | Y | 'a new reader is created for each company'; pause covers only that one reader |
| ans-11 | 6 | INCOMPLETE | Y | 'a rate-limit error (429)' only; omits RESOURCE_EXHAUSTED and thrown-error path |
| ans-11 | 7 | CORRECT | Y | Paid key only when all five cooling; 'at most 4 tries' stops before paid key |
| ans-11 | 8 | CORRECT | Y | Contains match over name, tags, city, sector label; description not searched |
| ans-11 | 9 | CORRECT | Y | Banner when lookup finds company with that domain and draft status |
| ans-11 | 10 | WRONG | Y | Exempts md/txt/rst, docs/, .memory, images beyond key's three folders |
| ans-11 | 11 | CORRECT | Y | Flags only when total assertion removals exceed additions across test files |
| ans-11 | 12 | CORRECT | Y | Lowered coverage minimum flagged; raised max-warnings or threshold flagged; tightening silent |
| ans-11 | 13 | CORRECT | Y | 'version changed', not 'version higher'; lower different version passes |
| ans-11 | 14 | CORRECT | Y | Timestamp excluded; generated 'at:' date counts as content |
| ans-12 | 1 | CORRECT | Y | '85 or more goes live, below 85 stays a draft'; foreign archived unless unreachable link (not in key) |
| ans-12 | 2 | CORRECT | Y | 'unless its apply link is explicitly flagged as not working'; nothing sets it false |
| ans-12 | 3 | CORRECT | Y | 15/7.5/3.75 title vs 5/2.5/1.25 department; department only for unmatched tier |
| ans-12 | 4 | CORRECT | Y | 'read from the source's own fields where the job feed has them, and otherwise ... title' |
| ans-12 | 5 | CORRECT | Y | Fresh extractor per company; pause does not carry over; run quota stop not triggered |
| ans-12 | 6 | CORRECT | Y | 429 or error mentioning RESOURCE_EXHAUSTED triggers cooldown; other errors do not switch |
| ans-12 | 7 | CORRECT | Y | 'at most 4 tries'; paid key only after all five free keys benched |
| ans-12 | 8 | CORRECT | Y | Contains match over name, tags, city, sector label; description not searched |
| ans-12 | 9 | CORRECT | Y | Banner when draft company matched; other status shows Already Registered |
| ans-12 | 10 | WRONG | Y | Exempts markdown, text, docs/, .memory, images beyond key's three folders and LICENSE/git files |
| ans-12 | 11 | CORRECT | Y | Flags when net assertion removals across test files; tests-removed exception row noted |
| ans-12 | 12 | CORRECT | Y | Coverage minimum lowered flagged; threshold raised flagged; tightening silent |
| ans-12 | 13 | CORRECT | Y | 'requires a different version, not a higher one'; lower different version passes |
| ans-12 | 14 | CORRECT | Y | Timestamp ignored; generated 'at' date counts as content |

## Summary

| ID | CORRECT | TRAP | WRONG | INCOMPLETE |
|---|---|---|---|---|
| ans-01 | 13 | 0 | 1 | 0 |
| ans-02 | 12 | 0 | 1 | 1 |
| ans-03 | 13 | 0 | 1 | 0 |
| ans-04 | 13 | 0 | 1 | 0 |
| ans-05 | 13 | 0 | 1 | 0 |
| ans-06 | 13 | 0 | 1 | 0 |
| ans-07 | 12 | 1 | 1 | 0 |
| ans-08 | 13 | 0 | 1 | 0 |
| ans-09 | 13 | 0 | 1 | 0 |
| ans-10 | 13 | 0 | 1 | 0 |
| ans-11 | 11 | 0 | 1 | 2 |
| ans-12 | 13 | 0 | 1 | 0 |
