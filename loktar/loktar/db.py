import pickle
import redis
import os


class Job(object):
    def __init__(self):
        self.host = os.environ.get("LOKTAR_JOB_DB_URI", "localhost")
        self.port = os.environ.get("LOKTAR_JOB_DB_PORT", 6379)
        self.db = os.environ.get("LOKTAR_JOB_DB_NAME", 0)
        self.expire = os.environ.get("LOKTAR_JOB_EXPIRE", 86400)
        self._db = redis.StrictRedis(host=self.host, port=self.port, db=self.db)
        self._pipeline = self._db.pipeline()

    def set_job(self, job_id, job_payload):
        return self._db.set(job_id, pickle.dumps(job_payload), ex=self.expire)

    def get_job(self, job_id):
        return pickle.loads(self._db.get(job_id))

    def get_jobs(self):
        for job_id in self._db.scan_iter():
            self._pipeline.get(job_id)

        return map(pickle.loads, self._pipeline.execute())
