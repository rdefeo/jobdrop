#!/usr/bin/env python
# encoding: utf-8
"""
import_occupation_data.py

Created by Roberto De Feo on 2013-03-18.
Copyright (c) 2013 __MyCompanyName__. All rights reserved.
"""

import sys
import os
import json
import requests
import datetime

version = '17.0'
jobdrop_url = 'http://127.0.0.1:5984/jobdrop/'
content_model_reference = {}
scales_reference = {}
task_statements = {}
job_zone_reference = {}

def get_document_id(onet_code):
  return 'od:%s' % onet_code

def get_document_url(onet_code):
  return '%s%s' % (jobdrop_url, get_document_id(onet_code))

def get_document(onet_code):
  r = requests.get(get_document_url(onet_code))
  if (r.status_code == 200):
    return json.loads(r.content)

def update_document(onet_code, document):
  r = requests.put(get_document_url(onet_code), data=json.dumps(document), headers = {'content-type': 'application/json'})

def import_occupation_data():
  lines = [line.strip() for line in open('data/Occupation Data.txt')]
  lines.pop(0)
  for line in lines:
    line = line.rstrip().split('\t')   
    document = get_document(line[0])
    if document and document['version'] != version and document['title'] != line[1] and document['description'] != line[2]:
      document['version'] = version
      document['title'] = line[1]
      document['description'] = line[2]
      document['last_update'] = str(datetime.datetime.now())
      update_document(line[0], document)
    else:
      j = json.dumps({'_id': get_document_id(line[0]), 
      'type': 'occupation_data',
      'title': line[1], 
      'description': line[2],
      'last_update': str(datetime.datetime.now()),
      'version': version
      })
      r = requests.post(jobdrop_url, data=j, headers = {'content-type': 'application/json'})
  
  print 'completed: import_occupation_data()'

def import_green_occupations():
  lines = [line.strip() for line in open('data/Green Occupations.txt')]
  lines.pop(0)
  for line in lines:
    line = line.rstrip().split('\t')   
    document = get_document(line[0])
    if document and (not document.has_key('green_occupational_category') or (document.has_key('green_occupational_category') and document['green_occupational_category'] != line[1])):
      document['green_occupational_category'] = line[1]
      document['last_update'] = str(datetime.datetime.now())
      update_document(line[0], document)
  print 'completed: import_green_occupations()'  

def import_job_zones():
  lines = [line.strip() for line in open('data/job zones.txt')]
  lines.pop(0)
  for line in lines:
    line = line.rstrip().split('\t')   
    # O*NET-SOC Code  Job Zone  Date  Domain Source
    document = get_document(line[0])
    job_zone = job_zone_reference[line[1]]
    if document and (not document.has_key('job_zone') or (document.has_key('job_zone') and document['job_zone'] != job_zone)):
      document['job_zone'] = job_zone
      document['last_update'] = str(datetime.datetime.now())
      update_document(line[0], document)
  print 'completed: import_job_zones()'  

def import_line(create, items_name, file_name):
  lines = [line.strip() for line in open(file_name)]
  lines.pop(0)
  for line in lines:
    line = line.rstrip().split('\t')   
    document = get_document(line[0])  
    if document:
      items = document[items_name] if document.has_key(items_name) else []
      item = create(line)
      if not item in items:
        items.append(item)
        document[items_name] = items
        update_document(line[0], document)
        print 'updating %s' % line[0]
    else:
      print 'missing soc code: %s' % line
  print 'completed: import_%s()' % items_name

def create_skill(line):
  skill = {'version': version, 'element_id': line[1], 'element_name': line[2]}
  skill.update(scales_reference[line[3]])
  skill.update({'data_value': line[4], 'sample_size': line[5], 'standard_error': line[6], 'lower_ci_bound': line[7], 'upper_ci_bound': line[8], 'recomended_suppress': line[9] == 'Y', 'not_relevant': line[10] == 'Y', 'domain_source': line[12] })
  return skill

def create_knowledge(line):
  knowledge = {'version': version, 'element_id': line[1], 'element_name': line[2] }
  knowledge.update(scales_reference[line[3]])
  knowledge.update({'data_value': line[4], 'domain_source': line[12] })
  return knowledge

def create_work_value(line):
  # O*NET-SOC Code  Element ID  Element Name  Scale ID  Data Value  Date  Domain Source
  work_value = {'version': version, 'element_id': line[1], 'element_name': line[2]}
  work_value.update(scales_reference[line[3]])
  work_value.update({'data_value': line[4], 'domain_source': line[6] })
  return work_value

def create_work_style(line):
  # O*NET-SOC Code  Element ID  Element Name  Scale ID  Data Value  N Standard Error  Lower CI Bound  Upper CI Bound  Recommend Suppress  Date  Domain Source
  work_style = {}
  work_style = {'version': version, 'element_id': line[1], 'element_name': line[2]}
  work_style.update(scales_reference[line[3]])
  work_style.update({'data_value': line[4], 'standard_error': line[6], 'lower_ci_bound': line[7], 'upper_ci_bound': line[8], 'recomended_suppress': line[9] == 'Y', 'domain_source': line[11]  })
  return work_style

def create_interest(line):
  interest = {'version': version, 'element_id': line[1], 'element_name': line[2]}
  interest.update(scales_reference[line[3]])
  interest.update({'data_value': line[4], 'domain_source': line[6]})
  return interest

def load_content_model_reference():
  lines = [line.strip() for line in open('data/Content Model Reference.txt')]
  lines.pop(0)
  for line in lines:
    line = line.rstrip().split('\t')
    content_model_reference[line[0]] = [line[1], line[2]]
  print 'completed: load_content_model_reference()'

def load_scales_reference():
  lines = [line.strip() for line in open('data/Scales Reference.txt')]
  lines.pop(0)
  for line in lines:
    line = line.rstrip().split('\t')
    scales_reference[line[0]] = {'scale_id': line[0], 'scale_name': line[1], 'scale_minimum': line[2], 'scale_maximum': line[3]}
  print 'completed: load_scales_reference()'

def load_task_statements():
  lines = [line.strip() for line in open('data/Task statements.txt')]
  lines.pop(0)
  # O*NET-SOC Code  Task ID Task  Task Type Incumbents Responding Date  Domain Source
  for line in lines:
    line = line.rstrip().split('\t')
    task = {'task_id': line[1], 'task_name': line[2], 'task_type': line[3], 'domain_source': line[6]}
    if line[4] != 'n/a':
      task.update({'incumbents': line[4]})
    task_statements[line[1]] = task
    
  print 'completed: load_task_statements()'
def load_green_task_statements():
  lines = [line.strip() for line in open('data/Green Task statements.txt')]
  lines.pop(0)
  # O*NET-SOC Code	Task ID	Task	Green Task Type	Date	Domain Source
  for line in lines:
    line = line.rstrip().split('\t')
    task = {'task_id': line[1], 'task_name': line[2], 'task_type': line[3], 'domain_source': line[5]}
    task_statements[line[1]] = task
  print 'completed: load_green_task_statements()'

def load_job_zones():
  lines = [line.strip() for line in open('data/job zone reference.txt')]
  lines.pop(0)
  # Job Zone	Name	Experience	Education	Job Training	Examples	SVP Range
  for line in lines:
    line = line.rstrip().split('\t')
    job_zone_reference[line[0]] = {'job_zone': line[0], 'zone_name': line[1], 'experience': line[2], 'education': line[3], 'job_training': line[4], 'examples': line[5]}
  print 'completed: load_job_zones()'

def main():
  load_scales_reference()
  load_content_model_reference()
  load_task_statements()
  load_green_task_statements()
  load_job_zones()
  # import_occupation_data()
  #   import_green_occupations() 
  import_job_zones() 
  # import_line(create_skill, 'skill', 'data/skills.txt') 
  # import_line(create_interest, 'interest', 'data/interests.txt')
  # import_line(create_knowledge, 'knowledge', 'data/knowledge.txt')             
  # import_line(create_work_value, 'work_value', 'data/work values.txt')             
  # import_line(create_work_style, 'work_style', 'data/work styles.txt')             
  

if __name__ == '__main__':
  main()

