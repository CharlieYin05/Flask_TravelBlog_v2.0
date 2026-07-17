# 修复无法Submit多天多活动的Bug

**日期**
2026-07-16

---

## 目标：
- 能正常Post Itinerary
- 如果不能Post要弹出提示

## 过程

### 1.Bug复现
- 用Chrome浏览器，Post一天一个Activity → 发布正常
- 用Chrome浏览器，Post一天四个Activity → 发布正常
- 用Chrome浏览器，Post两天六个Activuty，全写Description和每天选择食宿 → 发布正常
用Chrome浏览器，初步怀疑时Description和Other要全写，没写不让Post但是没有弹窗提示
- 用Chrome浏览器，Post两天六个Activity，不填写Description，不勾选交通和食宿 → Chrome会提示要交通和食宿 → 发布正常
进一步怀疑Safari问题
- 用Safari浏览器，Post两天六个Activity，不填写Description，不勾选交通和食宿 → 
