#!/usr/bin/python
# -*- coding: utf-8 -*-

import csv
import os
import re
from datetime import date
pre = './docs'

################################################################################

class AD(dict):
    """allows to access dict['item'] as obj.attr
    """
    def __getattr__(self, attr): return self[attr]
    def __setattr__(self, attr, value): self[attr] = value

def dict2lev_set(d,k0,k1,v):
    if k0 not in d: d[k0] = dict()
    d[k0][k1] = v

################################################################################

def read_csv(fn,formats,res):
    def split_row_by_empty_cells(row):
        groups = []
        curr_group = None
        for cn, val in enumerate(row):
            if not val: curr_group = None
            elif curr_group: curr_group.append((cn,val))
            else:     
                curr_group = [(cn,val)]
                groups.append(curr_group)
        return groups

    def identify_head(row):
        candidates_found = []
        for group in split_row_by_empty_cells(row): 
            identify_col_group(group,candidates_found)
        return candidates_found

    def identify_col_group(group,candidates_found):
        candidates = dict()
        for cn, val in group:
            if val not in formats.capt_index: continue
            for format_name, field_name in formats.capt_index[val].iteritems():
                dict2lev_set(candidates, format_name, field_name, cn)
                candidate = candidates[format_name]
                format = formats.formath[format_name]
                if len(candidate) < len(format.fields): continue
                candidates_found.append((format_name, candidate))
                return

    def read_data_row(candidates_found,rn,row):
        for format_name, candidate in candidates_found:
            format = formats.formath[format_name]
            rec = dict()
            try:
                for field_name, cn in candidate.iteritems():
                    raw = row[cn]
                    if not raw and not rec: continue
                    field = format.fields[field_name]
                    if not raw: 
                        raise Exception('нет значения поля '+field.caption)
                    rec[field_name] = format.fields[field_name].prep(raw)
                if rec: res[format_name].recv(**rec)
            except Exception as exc:
                warn('ряд '+str(rn)+', колонка '+str(cn)+', ['+raw+']: '+str(exc))
            
    
    def warn(txt):
        print txt
        """todo"""
    
    with open(fn,'rb') as csvfile:
        reader = csv.reader(csvfile,delimiter=',',quotechar='"')
        head = None
        for rn, row in enumerate(reader):
            if not head: head = identify_head(row)
            else: read_data_row(head,rn,row)
        if not head: warn('заголовочная строка не найдена')

################################################################################

def fill_capt_index(formats):
    capt_index = dict()
    for format_name, format in formats.formath.iteritems():
        for field_name, field in format.fields.iteritems():
            dict2lev_set(capt_index, field.caption, format_name, field_name)
    formats.capt_index = capt_index

################################################################################

def month_start(dt): return dt.replace(day=1)

################################################################################

class field_date(AD):
    def prep(self,str):
        ma = re.match(r"^(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})$",str)
        if not ma: raise Exception('неясное значения даты '+self.caption)
        return date(**{ k: int(v) for k, v in ma.groupdict().iteritems() })
class field_str(AD):
    def prep(self,str): return str
class field_int(AD):
    def prep(self,str): return int(str)
class field_money(AD):
    def prep(self,str): return float(str)
class field_options(AD):
    def prep(self,str): return self.options[str]

class holiday_keeper:
    def __init__(self): self.dt2free = dict()
    def recv(self,date): self.dt2free[date] = True
    def is_free_day(self,dt): return dt in self.dt2free
class absence_keeper:
    def __init__(self): self.by_employee = dict()
    def recv(self,employee,date_from,date_to,absence_type):
        if employee not in self.by_employee: 
            self.by_employee[employee] = employee_absences()
        self.by_employee[employee].add(date_from,date_to,absence_type)
class reward_keeper:
    def __init__(self): self.by_employee = dict()
    def recv(self,employee,year,month,amount_of_remuneration):
        if employee not in self.by_employee: 
            self.by_employee[employee] = employee_rewards()
        emp = self.by_employee[employee]
        emp.set_month_reward( date(year,month,1), amount_of_remuneration )

class employee_rewards:
    def __init__(self): self.mon2reward = dict()
    def get_month_hired(self,dt): return month_start(dt) in self.mon2reward
    def get_month_reward(self,dt): return self.mon2reward[month_start(dt)]
    def set_month_reward(self,dt,v): self.mon2reward[month_start(dt)] = v
    
class employee_absences:
    def __init__(self): 
        self.by_type = dict()
        self.dt2free = dict()
    def add(self,date_from,date_to,absence_type):
        if absence_type not in self.by_type: self.by_type[absence_type] = []
        self.by_type[absence_type].append((date_from,date_to))
        dt = date_from
        while dt <= date_to:
            self.dt2free[dt] = True
            dt += date.resolution
    def is_free_day(self,dt): return dt in self.dt2free

################################################################################

def fill_formats(formats):
    formats.formath = dict(
        holiday = AD(fields=dict(
            date = field_date(caption='дата праздникa'),
        )),
        absence = AD(fields=dict(
            employee = field_str(caption='работник'),
            date_from = field_date(caption='от, вкл'),
            date_to = field_date(caption='до, вкл'),
            absence_type = field_options(caption='тип отсутствия', options={
                'больничный (опл)': 'bo',
                'отпуск (опл)': 'oo',
                'другое' : 'etc'
            })
        )),
        reward = AD(fields=dict(
            employee = field_str(caption='работник'),
            year = field_int(caption='год'),
            month = field_int(caption='месяц'),
            amount_of_remuneration = 
                field_money(caption='сумма вознаграждений, EUR'),
        ))
    )

################################################################################

def main():
    formats = AD()
    fill_formats(formats)
    fill_capt_index(formats)

    res = AD()
    res.holiday = holiday_keeper()
    res.absence = absence_keeper()
    res.reward = reward_keeper()
    
    
    
    for fn in os.listdir(pre):
        if fn.endswith('.csv'):
            read_csv(pre+'/'+fn,formats,res)

    for employee, rewards in res.reward.by_employee.iteritems():
        if employee not in res.absence.by_employee: continue
        absences = res.absence.by_employee[employee] 
        
        for date_from, date_to in absences.by_type['bo']
            days = (date_to - date_from).days + 1
            pdays = 5 if days > 7 else days - 3 if days > 3 else 0
    
"""
    from pprint import pprint
    pprint(res.holiday.dt2free)
    pprint(res.absence.by_employee['Testing'].dt2free)
    pprint(res.absence.by_employee['Testing'].list  )
    pprint(res.reward.by_employee['Testing'].mon2reward  )
"""
if __name__ == "__main__": main()
