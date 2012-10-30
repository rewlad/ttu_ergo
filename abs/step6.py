#!/usr/bin/python
# -*- coding: utf-8 -*-

#./dev_appserver.py ~/ourdoc/ttu_ergo/abs
import re
import json
from datetime import date
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

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

def fill_data(data,formats,res):
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

    def identify_head(rn,row):
        candidates_found = []
        for group in split_row_by_empty_cells(row): 
            identify_col_group(rn,group,candidates_found)
        return candidates_found

    def identify_col_group(rn,group,candidates_found):
        candidates = dict()
        for cn, val in group:
            #logging.debug(val)
            #if rn<5: warn('CV:'+str(cn)+'['+str(type(val))+']')
            if val not in formats.capt_index: continue
            #warn('!!')
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
            rec = AD()
            try:
                for field_name, cn in candidate.iteritems():
                    format.fields[field_name].prep_outer(field_name,rec,row[cn],cn,res)
                if rec: 
                    rec.rn = rn
                    res[format_name].recv(rec)
            except Exception as exc:
                warn(u'ряд '+str(rn)+u', колонка '+str(cn)+', ['+str(row[cn])+']: '+unicode(exc))#+': '+str(exc)
            
    
    def warn(txt):
        res.warn += txt + "\n"

    head = None
    for rn, row in enumerate(data):
        if head: read_data_row(head,rn,row)
        else: head = identify_head(rn,row)
    if not head: warn(u'заголовочная строка не найдена')

################################################################################

def fill_capt_index(formats):
    capt_index = dict()
    for format_name, format in formats.formath.iteritems():
        for field_name, field in format.fields.iteritems():
            dict2lev_set(capt_index, field.caption, format_name, field_name)
    formats.capt_index = capt_index

################################################################################

def month_start(dt): return dt.replace(day=1)
def prev_month_end(dt): return month_start(dt) - date.resolution

def sum_for_prev_months(dt,n,f):
    if n <= 0 : return 0; 
    pdt = prev_month_end(dt)
    return f(pdt) + sum_for_prev_months(pdt,n-1,f)

def sum_for_month_days(dt,f):
    """ for days 1..dt.day """
    pdt = dt - date.resolution
    return f(dt) + ( sum_for_month_days(pdt,f) if dt.month == pdt.month else 0 )

################################################################################

class field_input(AD):
    def prep_outer(field,fn,bd,raw,cn,res):
        if not raw and not bd: return
        if not raw: raise Exception(u'нет значения поля '+field.caption)
        bd[fn] = field.prep(raw)
class field_output(AD):
    def prep_outer(field,fn,bd,raw,cn,res):
        out_task = AD( bd=bd, fn=fn, cn=cn )
        res.out_seq.append(out_task)

class field_date(field_input):
    def prep(self,str):
        ma = (
            re.match(r"^(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$",str) or
            re.match(r"^(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})$",str)
        )
        if not ma: raise Exception(u'неясное значения даты '+self.caption)
        return date(**{ k: int(v) for k, v in ma.groupdict().iteritems() })
class field_str(field_input):
    def prep(self,str): return str
class field_int(field_input):
    def prep(self,str): return int(str)
class field_money(field_input):
    def prep(self,str): return float(str)
class field_options(field_input):
    def prep(self,str): return self.options[str]
    
class holiday_keeper:
    def __init__(self): self.dt2free = dict()
    def recv(self,bd): self.dt2free[bd.date] = True
    def is_free_day(self,dt): return dt in self.dt2free
class absence_keeper:
    def __init__(self): self.by_employee = dict()
    def recv(self,bd):
        if bd.employee not in self.by_employee: 
            self.by_employee[bd.employee] = employee_absences()
        self.by_employee[bd.employee].add(bd)
class reward_keeper:
    def __init__(self): self.by_employee = dict()
    def recv(self,bd):
        if bd.employee not in self.by_employee: 
            self.by_employee[bd.employee] = employee_rewards()
        emp = self.by_employee[bd.employee]
        emp.set_month_reward( date(bd.year,bd.month,1), bd.amount_of_remuneration )

class employee_rewards:
    def __init__(self): self.mon2reward = dict()
    def get_month_hired(self,dt): return month_start(dt) in self.mon2reward
    def get_month_reward(self,dt):
        if self.get_month_hired(dt): return self.mon2reward[month_start(dt)]
        else: return 0
    def set_month_reward(self,dt,v): self.mon2reward[month_start(dt)] = v
    
class employee_absences:
    def __init__(self): 
        self.by_type = dict()
        self.dt2free = dict()
    def add(self,bd):
        if bd.absence_type not in self.by_type: 
            self.by_type[bd.absence_type] = []
        self.by_type[bd.absence_type].append(bd)
        dt = bd.date_from
        while dt <= bd.date_to:
            self.dt2free[dt] = True
            dt += date.resolution
    def is_free_day(self,dt): return dt in self.dt2free

################################################################################

def fill_formats(formats):
    formats.formath = dict(
        holiday = AD(fields=dict(
            date = field_date(caption=u'дата праздникa'),
        )),
        absence = AD(fields=dict(
            employee = field_str(caption=u'работник'),
            date_from = field_date(caption=u'от, вкл'),
            date_to = field_date(caption=u'до, вкл'),
            absence_type = field_options(caption=u'тип отсутствия', options={
                u'больничный (опл)': 'bo',
                u'отпуск (опл)': 'oo',
                u'другое' : 'etc'
            }),
            pdays = field_output(caption=u'дней к оплате'),
            m6_reward = field_output(caption=u'вознаграждения за 6 месяцев'),
            m6_days = field_output(caption=u'вознаграждаемых дней за 6 месяцев'),
            m6_reward_per_day = field_output(caption=u'вознаграждения за день'),
            to_pay = field_output(caption=u'расходы'),
        )),
        reward = AD(fields=dict(
            employee = field_str(caption=u'работник'),
            year = field_int(caption=u'год'),
            month = field_int(caption=u'месяц'),
            amount_of_remuneration = 
                field_money(caption=u'сумма вознаграждений, EUR'),
        ))
    )

################################################################################

def calc_absence_upkeep_for_employee(holiday,employee,rewards,absences):
    def reward_for_prev_6_months(date_from):
        get_month_reward = rewards.get_month_reward
        return sum_for_prev_months( date_from, 6, get_month_reward )
    
    def is_calwork_day_01(dt):
        if holiday.is_free_day(dt): return 0
        if absences.is_free_day(dt): return 0
        return 1
    def sum_month_calwork_days(dt):
        if not rewards.get_month_hired(dt): return 0;
        return sum_for_month_days(dt,is_calwork_day_01)
    def calwork_days_for_prev_6_months(date_from):
        return sum_for_prev_months( date_from, 6, sum_month_calwork_days )
    
    if 'bo' in absences.by_type:
        for bd in absences.by_type['bo']:
            days = (bd.date_to - bd.date_from).days + 1
            bd.pdays = 5 if days > 7 else days - 3 if days > 3 else 0
            bd.m6_reward = reward_for_prev_6_months(bd.date_from)
            bd.m6_days = calwork_days_for_prev_6_months(bd.date_from)
            bd.m6_reward_per_day = bd.m6_reward / bd.m6_days if bd.m6_days else '?'
            bd.to_pay = bd.m6_reward_per_day * bd.pdays * 0.7 if bd.m6_days else '?'
        
def main_operation(sdata):
    formats = AD()
    fill_formats(formats)
    fill_capt_index(formats)

    res = AD()
    res.holiday = holiday_keeper()
    res.absence = absence_keeper()
    res.reward = reward_keeper()
    res.warn = ''
    res.out_seq = []
    
    with open('holidays.json') as hfile: hdata = json.load(hfile)['data']
    fill_data( hdata, formats, res )
    fill_data( json.loads(sdata)['data'], formats, res )
    
    upkeep = []
    for employee, rewards in res.reward.by_employee.iteritems():
        if employee not in res.absence.by_employee: continue
        absences = res.absence.by_employee[employee] 
        calc_absence_upkeep_for_employee(
            res.holiday, employee, rewards, absences)
    
    
    out_seq = [
        dict(
            op='set',
            rn=task.bd.rn, 
            cn=task.cn, 
            val=task.bd[task.fn] if task.fn in task.bd else '?'
        ) 
        for task in res.out_seq if 'rn' in task.bd
    ]
    
    return json.dumps(dict(warn=res.warn,out_seq=out_seq))
    
    
    """
    print sum_for_prev_months(curr_date,1,sum_month_work_days)
    print sum_for_prev_months(curr_date,2,sum_month_work_days)
    print sum_for_prev_months(curr_date,4,sum_month_work_days)
    print sum_for_prev_months(curr_date,6,sum_month_work_days)
    """
        
    #from pprint import pprint
    #pprint(res.holiday.dt2free)
    #pprint(res.absence.by_employee['Testing'].dt2free)
    #pprint(res.absence.by_employee['Testing'].by_type  )
    #pprint(res.reward.by_employee['Testing'].mon2reward  )

#if __name__ == "__main__": main()

class json_handler(webapp.RequestHandler): 
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(main_operation(self.request.body))
 
run_wsgi_app(webapp.WSGIApplication(
    [('/absjson', json_handler)],
    debug=True
))
