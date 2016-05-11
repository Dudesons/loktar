import os
import pickle
import redis


class Job(object):
    def __init__(self):
        self.host = os.environ.get("LOKTAR_JOB_DB_URI", "localhost")
        self.port = os.environ.get("LOKTAR_JOB_DB_PORT", 6379)
        self.db = os.environ.get("LOKTAR_JOB_DB_NAME", 0)
        self.expire = os.environ.get("LOKTAR_JOB_EXPIRE", 86400)
        self._db = redis.StrictRedis(host=self.host, port=self.port, db=self.db)
        self._pipeline = self._db.pipeline()

    def set_job(self, job_id, job_payload):
        """Save job information in a db

        Args:
            job_id (str): the id of the current job
            job_payload (dict): the payload of the job who is store in the db

        Return:
             boolean, if the set on the db is ok True or if it failed False
        """
        return self._db.set(job_id, pickle.dumps(job_payload), ex=self.expire)

    def get_job(self, job_id):
        """Get a specific job payload

        Args:
            job_id (str): the id of the current job

        Return:
             dict, return the job payload
        """
        return pickle.loads(self._db.get(job_id))

    def get_jobs(self):
        """Get information on all jobs

        Return:
             list, who represents all payload for current job
        """
        for job_id in self._db.scan_iter():
            self._pipeline.get(job_id)

        return map(pickle.loads, self._pipeline.execute())
