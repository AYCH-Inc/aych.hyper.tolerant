from plenum.common.constants import CONFIG_LEDGER_ID
from plenum.server.batch_handlers.batch_request_handler import BatchRequestHandler
from plenum.server.database_manager import DatabaseManager


class ConfigBatchHandler(BatchRequestHandler):

    def __init__(self, database_manager: DatabaseManager):
        super().__init__(database_manager, CONFIG_LEDGER_ID)

    def commit_batch(self, three_pc_batch, prev_handler_result=None):
        res = super().commit_batch(three_pc_batch, prev_handler_result)
        self.database_manager.ts_store.set(three_pc_batch.pp_time,
                                           three_pc_batch.state_root,
                                           three_pc_batch.ledger_id)
        return res

    def post_batch_applied(self, three_pc_batch, prev_handler_result=None):
        pass

    def post_batch_rejected(self, ledger_id, prev_handler_result=None):
        pass
