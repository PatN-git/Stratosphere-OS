## 1
When a job is first written, it goes live only if its score is at least 85 and nothing disqualifies it. A score below 85, or any disqualifier (link invalid or marked unreachable, a talent-pool style title, a company-portal fallback link, or an unverified job category), makes it a draft. A job whose location looks foreign with no German region attached is archived straight away, unless its link is unreachable, which ranks higher and makes it a draft. A job that is already live under the same link is never demoted by a rescan. Later, a live job is archived if it is missing from two scans in a row (only counted when that company's scan returned at least one job), or if the daily link check finds a 404/410, "position filled" wording, a second failed check, or a posting older than 180 days.

## 2
The 10 points are added whenever the job is not explicitly marked as having a failed web check for its link. They only apply if the job already has a title longer than 2 characters and a valid http or https apply link, otherwise the whole score is 0. The scoring does not fetch the link itself. The adapters I read either set the flag to true or leave it blank, and I found nothing in the code that sets it to false, so a job that passes the basics normally gets the 10.

## 3
The title counts three times as much as the department. At each of the three keyword levels a title match scores 15, 7.5 or 3.75 points, while a department match scores 5, 2.5 or 1.25. The department only counts at a level if the title did not already match that level for the same category. A department keyword can also trigger the same 15-point penalty as a title keyword, and a category needs at least 4 points or the job is labelled "other". Several ATS adapters pass no department at all, so for those only the title is used.

## 4
They are worked out during extraction by keyword matching on what the source gives. Work mode comes from the source's workplace or location field when it has one, otherwise from words in the title such as remote, hybrid or on-site. Seniority (stored as experience) is mostly read from the job title, and some sources add their own experience field. Job type comes from the source's employment-type field, otherwise from the title. If nothing is recognised the value is left empty and costs score points, and when the row is saved it falls back to hybrid, experienced and full-time.

## 5
After a quota error (a 429 reply, or a reply whose text mentions "quota") the Gemini extractor stops asking the AI for 60 seconds, and in that time it returns no jobs. That pause is held inside that one extractor object. In the nightly run each company gets a fresh extractor, so the pause does not carry over to the next company. The run's own "stop on quota error" is separate and only triggers when an error carrying 429 is thrown out of an adapter, which this path does not do because it returns an empty result.

## 6
On every call the pool picks the free key that has been used least (the one used longest ago if tied), skipping any key that is cooling down, so it rotates even without errors. When a call gets a 429 (rate-limit reply, or an error mentioning 429 or RESOURCE_EXHAUSTED), that key is put on a 60-second cooldown and the same request is retried on another key. A request makes at most 3 attempts, or 4 if a paid reserve key is set (and never more than the number of keys). Other failures, such as timeouts or server errors, do not make it switch keys.

## 7
The paid key is only picked when every one of the five free keys is in its 60-second cooldown after a 429, and the paid key itself is not cooling down. Within a single request there are at most 4 attempts, and each 429 puts the tried key into cooldown. So a request that hits 429 on its first four free keys stops with a 429 error without reaching the paid key. The paid key is used when the free keys were already all cooling down from earlier requests.

## 8
It does a plain "contains" match, ignoring upper or lower case. Typing "solar" matches any company whose name, tags, city or sector label contains those letters anywhere, so a longer word like "Solarfabrik" would also match. A comma separates several search words, and a company shows if any one of them matches. The search then combines with the other filters, so a company must pass the sector, team size, funding and hiring filters too.

## 9
The banner appears after the user clicks "AI Auto-fill" with a website entered, and the lookup finds a company in the database whose website contains that domain and whose status is "draft". Only the first matching company is looked at, and if that one is not a draft the "Already Registered" banner shows instead. No banner appears if the lookup returns nothing, fails or times out (3 seconds). A repeat lookup that finds nothing removes it, and for a domain served from the 90-day saved lookup the company info comes from the saved copy, so it could be out of date.

## 10
The check runs on a commit and looks only at the files staged for that commit, not at unstaged changes. It skips docs and framework files (markdown, text, images, and anything under docs/, .memory/, .agents/, .claude/ and .github/ at the repo root, plus LICENSE files, .gitignore and .gitattributes), and also symlinks and submodules. Every other staged file, including deletions, must appear in the last passing test run recorded with exactly the same content. A file that was not in the run, or was changed after it, blocks the commit.

## 11
The guard counts lines that look like assertions (assert, expect(, .should, raises(, toThrow and similar) that were added and removed in test files since the point where the branch left the default branch. It only flags when the total across all test files is a net loss. When it is, it reports each test file that removed more assertion lines than it added. A loss in one test file is not flagged if other test files gained enough to offset it, and a "tests-removed" exception row merged on the default branch can exempt matching files.

## 12
It flags a change to a coverage minimum (such as fail_under, --cov-fail-under, lines, branches, functions, statements, or a Codecov target) when the value is lowered or the setting is removed. For a Codecov threshold or a max-warnings limit it flags a higher value or the setting being removed. It only reads specific config files (such as pytest.ini, pyproject.toml, package.json, and CI workflow files, with the JS coverage keys read from jest or vitest config and package.json, and the Codecov keys from the Codecov file). A brand-new threshold with no old one removed, a stricter value, or a path covered by a "threshold" exception row is not flagged.

## 13
Not strictly. The validator fails when a built document's content differs from the version at the point where the branch left the default branch but its version number is the same. A different number is enough, as long as it is in the x.y.z format, and it does not check that it is higher. It only compares documents that already existed at that point, so a brand-new document is not checked. A separate pull-request check does require the overall plugin version to be higher than the last release tag when shipped content has changed.

## 14
It depends on which date line. A date on a frontmatter line named timestamp is excluded from the content comparison, so editing only that does not count. The version line is excluded the same way. A date inside the generated block (its "at" line) or anywhere in the document body is not excluded, so editing only that does count as a content change and would need a new version number.
