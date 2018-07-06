"""
* > File: keep_survey_by_selenium.py
* > Date: 2018/07/05
* > Author: lamia
* > Rule: automatic write surveys to keep score 
    at a good level by selenium
"""
import os 
import re
import sys
import time
import copy
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


def logger(msg, show = True):
  """
  """
  if show:
    print(msg)
  return True


class KeepSurveyer(object):
  """
  """
  def __init__(self, show_gui = False):
    self._msg = None
    self._valid = False
    self._show_gui = show_gui
    self._survey_sort_id = 0
    self._main_page_url = None
    self._top_limit_score = None
    self._browser = None
    self.get_browser(show_gui)
    return
    
  def __del__(self):
    """ send email when destroyed
    """
    # self.send_email
    return
    
  def start(self, nonce = 5, show_gui = False):
    """ start
    """
    logger('start service')
    if show_gui != self._show_gui:
      self.get_browser(show_gui)
    self.set_top_limit_score(300)
    self.login()
    while True:
      t0 = time.time()
      self.goto_main_page()
      score = self.get_current_score()
      if self._valid is True:
        if self.goto_survey_page():
          self.write_and_submit()
      t1 = time.time()
      logger('processing time: {:.2f} seconds'.format(t1 - t0))
      self.sleep(nonce)
    return True
    
  def get_browser(self, show_gui):
    """
    """
    if show_gui:
      self._browser = webdriver.Chrome()
      self._browser.maximize_window()
    else:
      self._browser = webdriver.Remote(
        command_executor = 'http://127.0.0.1:5555/selenium/nogui_test_page', 
        desired_capabilities = DesiredCapabilities.HTMLUNIT)
    return True
  
  def set_main_page(self, url):
    """
    """
    self._main_page_url = url
    return True
  
  def login(self):
    """ 
    """
    users = [
      {
        'user': 'a', 
        'main_page': 'b', 
        'username': 'c', 
        'password': 'd.', 
      }, 
      {
        'user': 'a', 
        'main_page': 'b', 
        'username': 'c', 
        'password': 'd.', 
      }
    ]
    user = users[0] # select which user
    self.set_main_page(user['main_page'])
    self.goto_main_page()
    elem = self.elements_name('UserName')[0]
    elem.send_keys(user['username'])
    elem = self.elements_name('Password')[0]
    elem.send_keys(user['password'])
    elem = self.elements_name('LoginButton')[0]
    self.delay()
    if elem.is_displayed() and elem.is_enabled():
      elem.click()
    return True
  
  def goto_main_page(self):
    """ close other tabs and locate the main page
    """
    self.delay()
    if len(self._browser.window_handles) > 0:
      self.switch_tab(0)
      self._browser.refresh()
      cur_tab_size = len(self._browser.window_handles)
      for idx in range(cur_tab_size - 1, 0, -1):
        self.switch_tab(idx)
        self._browser.close()
      self.switch_tab(0)
    self._browser.get(self._main_page_url)
    return True
    
  def get_current_score(self):
    """
    """
    self.delay()
    try:
      elem = self.elements_class('link-UF90', self.elements_id('ctl02_ContentPlaceHolder1_lblRank')[0])[0]
      logger('rank: {}'.format(elem))
      self._rank = int(elem.text.replace('第', '').replace('名', ''))
      elem = self.elements_id('ctl02_ContentPlaceHolder1_lblCount')[0]
      score = int(elem.text.replace('点', ''))
    except:
      self._valid = False
      logger('reach max writing counts, try tomorrow and this script will detect in an hour')
      self.delay(3600)
      return self._top_limit_score
    if score > self._top_limit_score:
      self._valid = False
      logger('current rank: {}, score: {}, larger than limit: {}, wait until score goes down'.format(self._rank, score, self._top_limit_score))
    else:
      self._valid = True
      logger('current rank: {}, score: {}, smaller than limit: {}, go to write surveys'.format(self._rank, score, self._top_limit_score))
    return score
    
  def set_top_limit_score(self, score):
    """
    """
    self._top_limit_score = score
    return True
    
  def goto_survey_page(self):
    """
    """
    self.delay()
    self.switch_tab(0)
    self._survey_sort_id = 1 if self._rank == 1 else 0
    survey_link = self.elements_class('titlelnk')[self._survey_sort_id + 2]
    logger('survey name: {}'.format(survey_link.text))
    if 1 == len(self.find_content(survey_link.text, '(.*?)您的问卷')):
        self.delay(30)
        return False
    if survey_link.is_displayed() and survey_link.is_enabled():
      survey_link.click()
    self.switch_tab(1)
    elems = self.elements_class('finish')
    if len(elems) == 0:
      if elems[0].is_displayed() and elems[0].is_enabled():
        elems[0].click()
    return True
    
  def switch_tab(self, idx):
    """
    """
    self._browser.switch_to_window(self._browser.window_handles[idx])
    # logger('switch to tab: {}'.format(self._browser.title))
    
  def handle_alert(self):
    """
    """
    try:
      alert = self._browser.switch_to_alert()
      logger('found alert')
      alert.accept()
      return True
    except Exception as ex:
      pass
    return False
    
  def write_and_submit(self, qst_id = 0):
    """
    """
    self.delay()
    # logger('page source: \n{}'.format(self._browser.page_source))
    questions = self.elements_css('.div_title_question')
    question_size = len(questions)
    logger('question size: {}'.format(question_size))
    while True:
      qst_id += 1
      qst = self.find_next_question(qst_id)
      if qst is None:
        if qst_id > question_size:
          logger("reach max questions")
          break
        else:
          logger("pass question: {}".format(qst_id))
          continue
      if not self.block_in(qst, qst_id):
        return False
    self.delay(10)
    submit_btns = self.elements_class('submitbutton')
    if len(submit_btns) == 1:
      elem = submit_btns[0]
      if elem.is_displayed() and elem.is_enabled():
        elem.click()
    self.handle_alert()
    self._browser.close()
    self.switch_tab(0)
    return True
    
  def find_next_question(self, idx):
    """
    """
    # logger("locating next question, idx: {}".format(idx))
    qsts = self.elements_id('divquestion{}'.format(idx))
    qst = qsts[0] if len(qsts) ==1 else None
    if qst is None:
      logger('question idx: {} not found'.format(idx))
    return qst
    
  def block_in(self, question, question_id):
    """
    """
    question_src = question.get_attribute('innerHTML')
    logger('question id: {}, src: \n{}'.format(question_id, question_src))
    reg_expr = "<li style=(.*?)</li>"
    choices = self.find_content(question_src, reg_expr)
    choices_size = len(choices)
    if choices_size == 0:
      reg_expr = 'class="inputtext"'
      choices = self.find_content(question_src, reg_expr)
      choices_size = len(choices)
    logger('question id: {}, choices: {}'.format(question_id, choices_size))
    for choice_id in range(choices_size, 0, -1):
      # for single click
      xpath = "//a[starts-with(@rel, 'q{}_{}')]".format(question_id, choice_id)
      elems = self.elements_xpath(xpath, question)
      logger('xpath: {}, size: {}'.format(xpath, len(elems)))
      if len(elems) > 0:
        if elems[0].is_displayed() and elems[0].is_enabled():
          elems[0].click()
      else:
        # for off2, off4, sortnum
        if len(elems) == 0:
          class_name = ['off2', 'off4', 'sortnum']
          for cls in class_name:
            elems = self.elements_class(cls, question)
            logger('xpath: {}, size: {}'.format(cls, len(elems)))
            if len(elems) > 0:
              if elems[0].is_displayed() and elems[0].is_enabled():
                elems[0].click()
                break
        else:
          # for text input
          elems = self.elements_class('inputtext', question)
          logger('inputtext size: {}'.format(len(elems)))
          if len(elems) > 0:
            if elems[0].is_displayed() and elems[0].is_enabled():
              elems[0].send_keys('1')
      if self.handle_alert():
        break
    return True
    
  def elements_name(self, name, base_elem = None):
    """
    """
    zz = self._browser if base_elem is None else base_elem
    return zz.find_elements_by_name(name)
    
  def elements_id(self, idx, base_elem = None):
    """
    """
    zz = self._browser if base_elem is None else base_elem
    return zz.find_elements_by_id(idx)
    
  def elements_class(self, cls, base_elem = None):
    """
    """
    zz = self._browser if base_elem is None else base_elem
    return zz.find_elements_by_class_name(cls)
    
  def elements_css(self, css, base_elem = None):
    """
    """
    zz = self._browser if base_elem is None else base_elem
    return zz.find_elements_by_css_selector(css)
    
  def elements_xpath(self, name, base_elem = None):
    """
    """
    zz = self._browser if base_elem is None else base_elem
    return zz.find_elements_by_xpath(name)
    
  def find_content(self, data, reg_expr):
    """
    """
    content = re.findall(reg_expr, data, re.S|re.M)
    # logger('size: {}, type: {}, content: {}'.format(len(content), type(content), content))
    return content
    
  def delay(self, nonce = 1):
    """
    """
    return time.sleep(nonce)
    return True
    
  def sleep(self, nonce):
    """
    """
    logger('---------- launch a new request in {:.2f} seconds ----------'.format(nonce))
    logger('')
    time.sleep(nonce)
    return True
  
  
if __name__ =='__main__':
  """
  """
  ks = KeepSurveyer(show_gui = True)
  ks.start(nonce = 5, show_gui = True)
  