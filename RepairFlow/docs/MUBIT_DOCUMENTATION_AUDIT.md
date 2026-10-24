# Mubit documentation and integration audit — 24 October 2026

## Scope and limits
Read the current official full-text export:22navigation sections,3374lines, from https://docs.mubit.ai/llms-full.txt. Coverage: overview, quickstart, concepts, firstadapter, all provider/HTTP/framework/codingtool guides, requests, tasks/sessions, modelIDs, imports, project/member/key administration, APIreference and troubleshooting. Compared current implementation and prior console observations. Searched public Reddit, HackerNews, GitHub, StackOverflow, dev.to, Medium and HuggingFace. This cannot cover private Discord/support, unindexed/deleted posts or every historical page. Search surfaces older memorySDK pages outside current navigation; treat those as a different integration surface, not adapter gateway instructions.

## Findings

### Confirmed: gateway collection is connected correctly
Anthropic SDK uses https://api.mubit.ai/anthropic, Mubit key, supported Claude model, SDK retries disabled and bounded PydanticAI execution. Provider key belongs in console. Train requests record full input/output. Existing console records prove receipt, not quality. Code:backend/app/agents/mubit.py and report_task.py. Source:https://docs.mubit.ai/guides/connect-anthropic . No missing SDK wrapper requirement is documented for this gateway workflow.

### Confirmed: task fragmentation includes dynamic tools
Current coordinator construct_agent registers read_report/read_communication/list_case_events with prepare_missing_evidence, which can omit them based on snapshot content. Mubit groups by instructions,tools,toolchoice,outputformat and model. Consequently a stable prompt alone does not guarantee one coordinator task. Earlier prompt revisions also fragmented traffic; exact cause of each historical task requires old full contracts. Do not undo reliability guards merely to merge tasks. Focused report classifier uses stable instructions and one fixed report_decision tool, avoiding changing readtool menus.
Source:https://docs.mubit.ai/guides/tasks-and-sessions . Clarification: whitespace,numbers,dates,IDs in prompts receive normalization, and modeldate/latest suffixes are normalized. A versionnumber or datedalias alone is not sufficient explanation for a new task. Source:https://docs.mubit.ai/guides/model-ids .

### Confirmed: session diversity matters
Mubit holds test data aside by session. Coordinator uses percase Anthropic metadata.user_id: correct conversation grouping. Repeating onecase produces morecalls, not more independent sessions. Previous task6 had24kept examples across only2sessions. Lack of independent scenarios is a concrete weakness even when near25kept. Reporttask omits metadata; documented fallback uses instructions+firstusermessage, so distinct reports get natural session separation. Missing explicitmetadata is not itself a bug.
Source:https://docs.mubit.ai/guides/tasks-and-sessions .

### Important unresolved issue: evaluation routing with recording off
report_task dev/eval/shadow use x-middleware-record:off. This protects heldout content from collection, but APIreference explicitly states off also drops taskfingerprint. Public docs do not specify whether adapter matching/routing remains possible in that mode. Do not claim off definitely bypasses adapters, and do not assume it can benchmark them. Confirm with Mubit; first supported comparison is Trymodels on a passedversion, which explicitly trainsnothing. Preserve holdoutprivacy; do not switch full recording on to gain traceability. Requested model and gatewayrequestID are insufficient servedadapter evidence.
Sources:https://docs.mubit.ai/reference/api , https://docs.mubit.ai/guides/first-adapter .

### Confirmed limitation: local scoring is not correction ingestion
Expectedlabels stay local. CLI compares outputs but does not submit corrected targetanswers. ConsoleGood/Bad supports ratings; arbitrary comment-to-supervised-target ingestion is not established by current docs. We manually rated onebadreport with explanatorycomment; later console showed onerejected, but no proof a correction became trainedweights. Obtain supported corrected-target workflow from Mubit before claiming correction-driven updates.
Sources:https://docs.mubit.ai/guides/requests ; supplied hackathonguide explicitly flags this uncertainty.

### Confirmed: readiness is more than raw accuracy or25calls
25kept is a default initialtraining threshold, not guaranteedpass. Promptonly means no measured adapter advantage over base+prompt. Current workspace additionally showed minimum20judged examples, requiredqualitytargets and improvementgate; these are consoleobservations, not universal publicdefaults. 80% alone may not pass95% target. Current coordinator scores7.7%/13.3% remain unusable. Narrowing task helps learnability but can also make base+prompt competitive, so genuineadapter improvement must be measured, not assumed.
Source:https://docs.mubit.ai/guides/first-adapter .

### Review timing remains undocumented
No reviewduration/SLA found in current docs. Documented dailytraininglimits and trainingpauses do not explain a task with55waiting,4running,0overreviewlimit. API60minute timeout is not reviewtimeout. Marketing about templates training inminutes is not a reviewguarantee. Ask serviceoperator whether reviewers are makingprogress if state persists. More recordedcalls will not by themselves resolve an unobserved backenddelay.
Sources:https://docs.mubit.ai/troubleshooting , https://mubit.ai/pricing .

### Budget and serving claims require separate proof
Providerkey calls charge the provideraccount; Mubitbalance alone cannot establish remainingAnthropiccredit. Shared reservationledger is callcountguard, not moneyspent. No documented adaptermodelID can be substituted in our request. Supported publiccomparison is passedadapter inTrymodels; operationalrouting/versionselection and recordoff provenance need explicit confirmation. Do not promise serving inRepairFlow merely because an adapter passes.
Sources:https://docs.mubit.ai/admin/provider-keys , https://docs.mubit.ai/guides/model-ids .

## Decisions
Keep reportv2 contract frozen; leave broadcoordinator reliability safeguards intact. Preserveheldouts and labelbaselines honestly. No paidrequests or runtimechanges for this audit. Prepare examples offline; await reviewdiagnostic rather than endlesslyaddingtraffic. Before finalbenchmark, confirm nontraining adapterinvocation plus servedidentity. Before hackathondemo, establish supported replacementanswerfeedback and actual versionupdate.

## Questions for Mubit engineer (prepared, not sent)
1. Is reporttask ln_2595e659e1342478d5f8616d progressing? What causes55waiting/4running with0overreviewlimit and noacceptances?
2. Does x-middleware-record:off permit adapterrouting despite droppingtaskfingerprint? What is supported heldout evaluation path with servedadapter/version/fallback proof?
3. What supported interface submits corrected targetanswers rather than only Good/Bad ratings? Are comments used for trainingtargets or only review?
4. What minimumsessions/judgedcases and improvementgate apply to thisworkspace? Can a highqualitybase+prompt result be used, and how is that distinguished from trainedadapter success?
5. After passing, how is the adapter activated for our Anthropic gateway calls and actual servedversion verified?

No external message sent. No credentials belong in this diagnostic.

## Public search evidence
Approximately23targeted searches covered Reddit,HackerNews,GitHub,StackOverflow,dev.to,Medium,HuggingFace and Mubit/Mubit.ai/MubitLabs variants. No relevant indexed firsthand report established normal gatewayreview duration or a queueworkaround. No inference that private/unindexed discussions do notexist.
- Currentgateway docs:https://docs.mubit.ai/guides/first-adapter
- Older memorySDK surface:https://docs.mubit.ai/getting-started and https://docs.mubit.ai/sdk/framework-integrations . Memoryreflection/recall requirements are not established gatewayrequirements.
- Official publicrepositories:https://github.com/mubit-ai ; https://github.com/MubitLabs/minima/issues ; https://github.com/MubitLabs/mintlify-docs/issues ; https://github.com/MubitLabs/mubit-cl-bench/issues . Visible issues supplied no currentreviewdelay diagnosis.
- HistoricalMinima changes:https://github.com/mubit-ai/minima/blob/main/CHANGELOG.md . Differentproduct/version; do not attribute its historicalbugs to currentgateway.
- Pricing:https://mubit.ai/pricing . Template-inminutes wording ismarketing, notreviewSLA; actualworkspace/hackathon termscontrolspend.
- Hackathon:https://luma.com/nightshift-london . No reviewtimepromise found.

Fullcurrentdocumentation reading completed across parent and one reviewer; publicsearch independently reviewed. No runtimecode changes or paidinference duringaudit.
