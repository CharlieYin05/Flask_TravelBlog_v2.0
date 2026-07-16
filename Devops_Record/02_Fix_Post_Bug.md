# 修复无法Submit多天多活动的Bug

**日期**
2026-07-16

--

## 目标：
- 能正常Post Itinerary
- 如果不能Post要弹出提示

## 过程

### 1.Bug复现
- Post一天一个Activity（正常）
- Post一天四个Activity（正常）
- Post两天六个Activuty，全写Description和每天选择食宿（正常）
- 初步怀疑时Description和Other要全写，没写不让Post但是没有弹窗


