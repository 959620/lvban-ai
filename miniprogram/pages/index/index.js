Page({
  data: {
    features: [
      { title: "智能追问", desc: "信息不完整时，AI 会主动补齐预算、人数与偏好。" },
      { title: "区域化路线", desc: "同区景点同天安排，减少来回折返与无效交通。" },
      { title: "预算拆分", desc: "住宿、交通、餐饮、门票一目了然，实时看剩余。" },
      { title: "美食推荐", desc: "按每日行程地点推荐早午晚餐与咖啡店。" },
      { title: "备用方案", desc: "下雨、太累、景点关闭都有替代行程。" },
    ],
  },
  goCreate() {
    wx.switchTab({ url: "/pages/create/create" });
  },
  goDemo() {
    wx.navigateTo({ url: "/pages/detail/detail?id=trip-dali-demo" });
  },
});
