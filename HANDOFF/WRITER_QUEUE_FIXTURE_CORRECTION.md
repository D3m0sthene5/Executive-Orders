# Native fixture dependency correction

The first actual Linux Road run127023667483 on9150192 passed the pre-existing suites but failed both new native fixture executions because jobs/_lib/cache_cap.py was absent from the isolated repository. The fixture now copies the real shared library alongside the real runner scripts, preserving native cache setup and its checks. No production workflow, runtime, freshness guard or scientific source changes in this correction. No local pass is claimed; fresh actual platform checks are required.

Old-version main reporter41958411273 has completed, so its old unqueued writer is no longer an active migration hazard. Its failed publication remains retained, not inferred successful.
