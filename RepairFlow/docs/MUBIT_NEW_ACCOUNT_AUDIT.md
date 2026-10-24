# New Mubit account diagnostic audit

Checked24October2026,17:34–17:36BST. Read-only browser inspection; no paid requests or settings changes.

## Confirmed outcome
No adapter exists. Adapters page explicitly states: “No adapters yet” and classifier trains at25kept examples, currently0. Taskln_28b32f28e9d7f4231463494a has now been created inprojectws-9ea386dc56aefa33. Training notstarted; routesnone. No learningsyet.

## Evidence and discrepancies
- Requests afterrefresh:87calls, upfrom10. Loaded all87available rows viaLoadmore withErrorsonly:0HTTP400+errors. This doesnotcover recordsnotyetvisible.
- Tasklist/traffic:103calls, grouped bysameinstructions/tools. Taskdetailheader and usablecountstill10; examples0kept,0rejected,13waiting;10queued,0overdailyquota,1running. These mutuallyinconsistent counts indicate delayed or inconsistent UI/backend aggregates; exact causeunknown.
- Reviewhistory:10newcalls sentforreview, approximately3minutesearlier. No completionor explicitreviewerror shown.
- Local evidence:200successful newkey requests,195expectedmatches, allrecordmodefull and requestIDs. UIhasnotyetconfirmed ingestionofall200; do notclaimallaccepted orlost.
- Anthropicproviderkey markedValid. Mubitkey previouslyverifiedActive/lastused. Noauthenticationerror found.
- Billing shows$50Mubitbalance andnocard. Onboarding stillasksSetupbilling. Noexplicittrainingpaymentblockshown; nocard aloneisnotestablishedcause. Thisbalance doesnotestablishAnthropicspend.
- Trainingpolicy:newversion25examples,examplelimit256KB,no dailytrainingstartlimit. Prioradvancedinspection:trainingenabled,reviewcap200/day,no trainoptout; qualitythresholds unchanged.
- Notifications panel showedNone. Learningspage brieflyshowed “Notification count may be incomplete”; reopeningnotifications removedwarningandshowedNone. PreserveastransientUIwarning,notproofhealthybackend.
- Browserdevlogs readatproviderpage:emptyerror/warninglist. FooterServiceOperational; notprooftrainingworkerhealthy.

## What is blocking progress
The immediate visible prerequisite is0acceptedexamples against25needed. Review and recordaggregationhave begun butareincomplete. Thereisno confirmeduser-side authenticationfailure,disabledtraining,quotaexcess orpaymentblock fornewproject. We cannot conclude everyintegrationdetailiscorrect orMubitworkersarestuck fromtheseUIobservationsalone.

## Next action
Stoppaidcollection. Monitorwhetherrecordcountreaches200andreviewproduceskept/rejectedresults. Ifcountsremainstalled, usepreparedsupportdiagnosticwithproject/taskIDs,requestIDsandtimestamps; nosupportmessagesent. AskMubitwhy200successful fullrecord responsesareonlypartiallyvisible andwhyreviewsremaininflightwithoutkept/rejectedresults. Do notlowerqualitybaroractivatefailedmodels.

Evidencefiles: docs/demo-evidence/new-account-task-audit.txt, new-account-learnings-audit.txt, new-account-adapters.png. Rawrequestmetrics:backend/data/report-task-runs/fresh-20261024-new-account-complete-summary.json andperbatchresults.
