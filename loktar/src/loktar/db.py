from loktar.constants import RUN_DB
from loktar.log import Log

from elasticsearch import Elasticsearch

logger = Log()


class Run(object):
    def __init__(self):
        self.host = RUN_DB["host"]
        self.port = RUN_DB["port"]
        self.db = RUN_DB["db"]
        self.table = RUN_DB["table"]
        self._db_connection = Elasticsearch(host=self.host, port=self.port)

    def set_run(self, job_payload):
        """Save job information in a db

        Args:
            job_payload (dict): the payload of the job who is store in the db

        Return:
             the id of the job document
        """
        result = self._db_connection.index(index=self.db, doc_type=self.table, body=job_payload)
        logger.info("Run indexation id:{}, shards_successful:{} shards_failed:{}".format(result["_id"],
                                                                                         result["_shards"]["successful"],
                                                                                         result["_shards"]["failed"]))
        return result["_id"]

    def get_run(self, job_id):
        """Get a specific job payload

        Args:
            job_id (str): the id of the current job

        Return:
             dict, return the job payload
        """
        result = self._db_connection.get(index=self.db, doc_type=self.table, id=job_id)
        logger.info("Get run with id: {}".format(result["_id"]))
        return result["_source"]

    def get_runs(self, page=0, size=10):
        """Get information on all jobs

        Return:
             list, who represents all payload for current job
        """
        result = self._db_connection.search(index=self.db,
                                            doc_type=self.table,
                                            from_=0 if page == 0 else (page + 1) * size,
                                            size=size,
                                            sort="start_time:desc")

        logger.info("The runs requests took {}ms for a size of {}".format(result["took"], size))

        return [hit["_source"] for hit in result["hits"]["hits"]]

