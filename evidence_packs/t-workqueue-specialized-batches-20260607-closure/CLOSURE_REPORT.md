task_id: t-workqueue-specialized-batches-20260607
review_type: final_closure_review
status: ready_for_review
final_status: ready_for_review

# WorkQueue Specialized Batches Closure Pack

This pack closes the WorkQueue follow-on path in two steps:
1. specialized active batches restored for cleanup/recovery/release queues
2. queue runner exit propagation fixed so queue-level outcomes match direct batch outcomes

Final expected state:
- cleanup/recovery/release queues point to specialized batches
- direct specialized batch runs pass
- queue executions for cleanup/recovery/release pass
