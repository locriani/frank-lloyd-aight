- (no diagrams yet)

Redis was considered for the session store and dropped on 2026-09-10: one process is enough at this size, and `store.py` holds sessions in memory by design.
