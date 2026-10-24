# Adapter recovery plan — 24 October 2026

## Success criteria
A Mubit adapter version passes its own quality gate, is available for serving/comparison, and performs well on independent, previously unseen repair cases. Prompt-only results and teacher fallback do not count as learned-adapter success. Record actual serving identity, quality, safety errors and spend where measurable.

## Stages
1. Inspect current adapter evaluation, task/retraining status and credit. Explain Prompt only accurately: no measured advantage over the base with prompt. Preserve failed results; do not force rollout or lower thresholds.
2. Build a stable, bounded report interpretation task within the existing PydanticAI architecture, initially isolated from operational decisions. Input one scope plus contractor report; output one of seven fixed classifications. Do not learn random IDs or arbitrary read-tool sequences.
3. Author distinct synthetic training/development/evaluation sets. Keep original40 coordinator holdouts untouched; no expected labels in prompts. Development calls recordoff, training full, final evaluation off.
4. Test offline transport, budget, stable contract, data splits and error handling. Independent review before paid collection.
5. Run small development batch; correct task/data defects before training. Expand only if correct and safe. Use shared reservation ledger with an explicit bounded per-experiment ceiling; do not raise operational cap or purchase credits. First intended experiment under120 short requests, inputs under6000chars, max256output tokens, at most2requests perdecision. Inspect counts/errors between batches.
6. Send diverse training examples in stages; verify Mubit groups them as one task and actually keeps them. Inspect low-quality outputs and existing feedback controls. Stop unnecessary collection once review/training is the bottleneck.
7. Inspect new version and failure examples. Iterate only from training/dev evidence, never tune against the final holdout. Keep old failed experiments in the record. Do not lower the readiness target.
8. Once servable, compare adapter and teacher on the independent eval set. Require zero unsafe false-completion in safety cases, report per-category accuracy and fallback separately. Small-sample uncertainty remains explicit.
9. Only integrate a validated model branch after preserving report eligibility, evidence references, policy/executor validation and clear fallback reporting. Rehearse real demo path on separate database.

## External dependency
Mubit owns training/serving. No public manual training-retry endpoint is documented. If a quota, unavailable backend or persistent failed version prevents progress, preserve evidence and prepare an exact support question. No external support message is sent without authorization. Balance currently shows $50, which does not establish Anthropic-account spend; respect user's $25 spend constraint and avoid long coordinator batches.

## 2026-10-24 14:20 UTC execution evidence

- New standalone report classifier: fixed seven-class tool output; no operational DB changes.
- Corpus: 56 train, 14 development, 28 untouched evaluation; balanced interleaved classes.
- First development v1: 12/14; clarified ambiguity precedence; frozen v2: 14/14.
- Recorded v2 training: 55/56 correct, 56 calls, 61,939 input + 2,247 output tokens. No retries/errors.
- Incorrect scaffold-scope answer rated Bad in console with correction; console request 01a16e47-3c67-7ec0-9404-98b1a9888779. Rating does not itself prove exclusion from training.
- Run artifacts: backend/data/report-task-runs/20261024T141730-82f7261e (dev v1), 20261024T141803-35c254d3 (dev v2), 20261024T141822-29d8bdae (train).
- Shared cumulative reservations now 253; operational ceiling adjusted180→264 to preserve exactly11 previously available operational reservations after84 short experiment calls. Ledger not reset. Backend restarted on original demo DB, no-contact mode.
- 431 backend tests passed. Python and general code reviews approved bounded experiment; actual adapter/version provenance is required before claiming adapter accuracy.
- Coordinator7 adapter ad_lane_6a4b3372 now exists: 2/15=13.3% vs base+prompt0%, target95%; schema100%; needs20 judged examples minimum. Not ready or routed. This is genuine measured improvement but nowhere near usable accuracy.
- Project training starts have no daily limit; new version threshold25kept. Recorded report calls initially show Not in a task yet; waiting for task assignment/review.
- Total new experiment calls84, tokens91,957 input +3,369 output; teacher results only. Heldout evaluation not run.

## Focused application integration decision — 14:47 UTC
User authorized reshaping agent requests around a useful task that can reach80%+ and pass Mubit readiness. Design: docs/superpowers/specs/2026-10-24-focused-adapter-design.md. Keep report-classification-v2 frozen. Add default-off shadow connection to authoritative pending reports; preserve existing operational decisions until actual adapter validated.
Console confirmed report task ln_2595e659e1342478d5f8616d:56usable calls,0kept,1rejected,55waiting;55queued,0overdaily reviewlimit,4running. No training yet. This is active review, not missing examples. Avoid further paid collection pending results.

Integration validation:445backend tests passed in31.79s; general and Python reviewers approved default-off shadow branch. No new paid requests in this integration turn. Shadow has at most90s synchronous added latency when deliberately enabled. It does not replace coordinator or prove adapter quality. Serving activation remains gated on actual passing adapter and independent evaluation.

## Next targeted round — 14:58 UTC
User reaffirmed target80–90% and delegated training choices. Prioritize frozen report task; prepare49additional independent trainonly examples and richer percategory/error metrics offline. Do not send pending batch while existing55examples remain unreviewed. See MUBIT_REPORT_REVIEW_STATUS.md for specific queued review evidence and unsent support diagnostic. Supplemental data changes must not mutate base eval set or modelcontract.

Prepared49 trainonly expansion cases in backend/app/report_training_expansion.py, reviewed against frozen v2. CLI --dataset expansion --split train supports dryrun; select balanced7-case batches when justified, not all49bydefault. Metrics nowperclass/confusion/errors/safety. No paidcalls.457full tests passed before finaladded interleavingtest;22focusedpassedafter. Data-author inspection inadvertently displayed existing heldoutentries; no eval inputs were used for modelprompt tuning or sent to models, and author states expansionindependent. For strongest final blind comparison, author a fresh independent testset after freezing the trainedcandidate.

## Mandatory pre-evaluation audit findings
Read MUBIT_DOCUMENTATION_AUDIT.md before next adapterbenchmark. record=off drops taskfingerprint; adapterrouting effects undocumented. Do not assume reportCLI can measure adapter merely because it usesgateway. Use passedversion Trymodels first or obtain confirmed nontraining servingpath with version/fallbackidentity. Local expectedlabels and Badcomments are not proven replacementtarget ingestion. Dynamiccoordinator toolmenus can fragmenttasks even at frozenprompt. Publicsearch found no supported reviewqueue workaround. Supportquestions prepared, unsent.

## Scheduled check — 24 October 2026 15:22 UTC
Report task unchanged:0kept,1rejected,55waiting;55queued,0overlimit,4running; first trainingnotstarted. History review event53minutes ago. Existing adapters unchanged7.7%/13.3%, bothnotready, no deployments. No newpaidcalls, heldoutuse or configurationchanges. No new actionable result; retain hourlyfollowup and preparedsupportquestions.

## User-authorized additional collection — 24 October 2026
User explicitly requested300–400more short normal-app requests and confirmed proceeding despite pending review. Run300 frozen report-classification-v2 decisions in five60-case batches. New corpus:60 authored scenariofamilies×5languagevariants; not300independent scenarios. Sevenclasses covered in eachbatch; no heldout selected/submitted. General/Pythonreview approved labels/CLI/budget safeguards;24relatedoffline tests passed. Startsharedledger253; experimentceiling553. Preserve existing11operational reservations afterward without resettingledger. Record teacher/unverifiedserving quality and actualrequests; do not claim trainedadapter accuracy. Stop on gateway failures/unsafe outputs. This single authorized batch does not authorize automatic endless paidcollection. Application decisionbehavior unchanged.

### Additional collection completed — 16:38 BST
All300 additional requests completed,293/300 expected labels matched;0errors/retries;40/40hazards correct.331586input+12032outputtokens. See MUBIT_BULK_COLLECTION.md and backend/data/report-task-runs/bulk-20261024-summary.json. Sevenmismatches retained; one ratedBad with correction inconsole. Console traffic310 (header56),0kept,reviewpending; assignment/aggregationdelayed. Ledger553,operationalcap564 preserves11remaining; same no-contactdemoDB backendhealthy. No morepaidcollection fromthisbatch; waitforreview/trainingevidence. This97.7% is teachertrainingagreement, NOT adapteraccuracy. Preserve28eval.

## Live outcome check — 24 October 2026 16:50 BST
Console now confirms all356 classifier calls (original56+additional300),356usable. Still0kept,2rejected,354waiting; reviewtoday200queued,154over today'slimit,12running. New reviewer history event7minutesago:145newcalls,0kept/0rejected. Firsttrainingnotstarted, routesnone. Dailyreviewlimit is now an explicit blocker for154calls; do notsendmorepaidrequests. Prior zero-overlimit observation no longercurrent. No passingclassifieradapter evidence.

## Fresh key experiment — 24 October 2026 17:25 BST
User updated root.env and authorized200freshpolished requests. Configuration mistake:runner initiallyreadprevious backend.envkey;100calls sentbefore detectingnewaccountzero/keyunused. Correctedbackendkeyfromroot.env; newaccountTerdessa/projectws-9ea386dc56aefa33 keythenlastusedjustnow. Sent100morewithnewkey. Total200calls:98/100previouskey,97/100newkey;0errors/retries. SeeMUBIT_FRESH_COLLECTION.md. Ledger753,operationalcap764,backendPID50338healthy/no-contactdemoDB. Newaccountreceived100NOT200. Askeduserapprovalfor100additionalreplays tocompletetheintended200innewaccount; pending, noautoreplay. Preserveallheldouts. Monitornewaccounttaskgrouping/review aswellasexistingaccountwhenaccessible; noadapteraccuracyclaim.
NewprojectRequests UI at17:24BST shows7records,not100; allYourprovider/200/unassigned.100successfulnewkeyAPIresponses areverified locally, but fullconsoleingestion notyetverified. Investigate delayed/missingrecording beforemorepaidcalls.

## Approved replay completed — 17:30 BST
User explicitlyapproved100additionalcalls. Newkeynow200unique scenarios answered195/200correct,0errors/retries,28/28hazards; artifactfresh-20261024-new-account-complete-summary.json. Totalexperiment300requests including100previous-key mistake. Ledger853/cap864,11operationalleft,backendcorrectkey/no-contactDB. Newconsoleonly10recorded/unassigned atlatestcheck: full200ingestionnotproven. No furtherpaidcalls; investigate discrepancy/readiness. Follow-upautomationupdated tocurrentnewproject andnonrepeatingcollectionguard.

## New-account UI audit — 17:34–17:36 BST
SeeMUBIT_NEW_ACCOUNT_AUDIT.md. Taskcreatedln_28b32f28e9d7f4231463494a;traffic103,header/usable10,0kept/0rejected/13waiting,10queued/0overlimit/1running. No adapter (explicitpage),firsttrainingnotstarted,routesnone,nolearnings.87recordedrequests inspected0HTTPerrors. AnthropicValid,$50Mubitcredit,nocardbutnoexplicitbillingblock. NotificationsNonewithbriefincompletecountwarning;browsererrorlogsempty. Aggregationprogress10→87→103 disprovesunchangedrecordingcountbutnotfull200ingestion. No paidcalls/settingschanges. Preservethresholds/holdouts; monitornewtask.

## Original account breakthrough — 24 October 2026 17:50 BST
Signed intooriginalaccountwithuserprovidedOTP. Newclassifieradapterad_lane_7ba3cee7 v1,Qwen3-4B-Instruct-2507,existsandhasmeasured83.3%(10/12) vsbase+prompt41.7%(5/12). Target85%;livealso requires20judgedcases,current12. Notready/noroute/nodeployment. Evalcomparesrecordedprovideranswers;providerlivebenchmark/schema validitynotmeasured. ThisisMubitinternaltestresult,notourindependentheldoutbenchmark. SavedUIevidence docs/demo-evidence/original-classifier-evaluation.txt.
Taskln_2595e659e1342478d5f8616d now55kept,2rejected,399waiting,55sessionswithkept. Traffic456;header/usable361(staleaggregate). Reviewtoday200queued,159overlimit,9running,1failed. Firsttrainingstarted33minutesprior;ftjob_57582cab. Coordinatoradaptersunchanged7.7%/13.3%. No paidcalls/noactivation/thresholdchanges. Preserve28eval; investigatefailedreviewandremainingqualitygate beforebenchmark. Currentbrowserloggedoriginal; backendkeyremainsnewaccount.

## Scheduled check — 24 October 2026 18:23 BST
Console is signed out; Signin opens email form, no saved session available. Cannot verify eitheraccount's current state without interactive login. No newOTP requested, paidcalls made, or heldouts used. Lastconfirmed originalclassifier83.3%/12cases remainshistoricalevidence,notfreshstatus. Usernotification requests sign-in toresume monitoring.

## Live check — 24 October 2026 18:30 BST
Original account refreshed:classifierstillv1 83.3%/12cases,target85%,notready;coordinators7.7%/13.3%,nodeployments.55kept/2rejected/399waitingunchanged. Reviewnow8running/2failed(previous9/1),200queued/159overlimit. Latestreviewevent28minutesago0new/0kept/0rejected. No newpassingadapter,paidcallsoractivation. Twofailedreviewjobsnowvisible; underlyingcauseunexposed in taskdetails.

## Scheduled check — 24 October 2026 19:41 BST
Current in-app tab explicitly reports session ended and requires sign-in. No live adapter/review data could be read; historical83.3% remains unrefreshed. NoOTPrequested,paidcalls,changesorheldoutuse. Existing sign-in dependency alreadyreported; avoidanotherunchangednotification.
