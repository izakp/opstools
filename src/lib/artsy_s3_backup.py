import logging
import os
import pytz

from datetime import datetime

from lib.date import over_ndays_ago
from lib.s3_interface import S3Interface

class ArtsyS3Backup:
  ''' manage backing up to Artsy S3 buckets '''
  def __init__(
    self,
    s3_bucket,
    s3_prefix,
    filename_suffix
  ):
    self._full_prefix = s3_prefix
    self._s3_interface = S3Interface()
    self.filename_suffix = filename_suffix
    self.s3_bucket = s3_bucket

  def _backup_id_to_s3_key(self, id):
    ''' convert backup id to s3 key '''
    key = os.path.join(
      self._full_prefix,
      f"{id}.{self.filename_suffix}"
    )
    return key

  def _backup_id(self):
    ''' generate and return a backup id '''
    backup_date = datetime.utcnow()
    # include timezone info
    backup_date_with_tz = backup_date.replace(tzinfo=pytz.utc)
    backup_date_str = str(backup_date_with_tz)
    backup_id = backup_date_str.replace(' ', '_')
    return backup_id

  def _is_backup(self, key):
    ''' return true if key is a backup '''
    return self.filename_suffix in key

  def _s3_key_to_backup_id(self, key):
    ''' convert s3 key to backup id '''
    file_name = key.replace(f"{self._full_prefix}/", '')
    id = file_name.replace(f".{self.filename_suffix}", '')
    return id

  def backup(self, source_file):
    ''' backup a file to S3 '''
    id = self._backup_id()
    key = self._backup_id_to_s3_key(id)
    logging.info(
      f"Copying {source_file} to s3://{self.s3_bucket}/{key} ..."
    )
    self._s3_interface.put_file(source_file, self.s3_bucket, key)

  def backups(self):
    ''' return backups, most recent first '''
    logging.info(
      f"ArtsyS3Backup: listing backups in " +
      f"s3://{self.s3_bucket}/{self._full_prefix}/"
    )
    objects = self._s3_interface.list_objects(
      self.s3_bucket, self._full_prefix
    )
    backups_found = []
    if 'Contents' in objects:
      keys = [o['Key'] for o in objects['Contents']]
      are_backups = [k for k in keys if self._is_backup(k)]
      ids = [self._s3_key_to_backup_id(k) for k in are_backups]
      backups_found = sorted(ids, reverse=True)
      logging.debug("ArtsyS3Backup: Found backups: {backups_found}")
    else:
      logging.info("ArtsyS3Backup: No backups found.")
    return backups_found

  def created_at(self, id):
    ''' return creation date string of given backup id '''
    timestamp = id.replace('_', ' ')
    return timestamp

  def delete(self, id):
    ''' delete the backup identified by id '''
    key = self._backup_id_to_s3_key(id)
    self._s3_interface.delete_object(self.s3_bucket, key)

  def old_backups(self, ndays):
    ''' return backups older than ndays '''
    backups = self.backups()
    old = []
    for backup in backups:
      id = backup.split('/')[-1]
      created_at = self.created_at(id)
      logging.debug(
        f"ArtsyS3Backup: backup with id {id} was created at {created_at}"
      )
      if over_ndays_ago(created_at, ndays):
        old += [backup]
    return old
