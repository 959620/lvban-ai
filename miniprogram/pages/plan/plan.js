const {
  companionLabels,
  formatCurrency,
  intensityLabels,
  preferenceLabels,
} = require("../../utils/labels");
const {
  appendMessage,
  getTrip,
  mockAssistantReply,
  regenerateTrip,
  updateTripRequest,
} = require("../../utils/store");

const quickPrompts = [
  "删除第二天骑行，改成轻松散步",
  "把午餐换成更便宜的本地小吃",
  "整体预算再降低 15%",
  "每天行程减少一个景点",
  "把 Day 2 换成下雨天方案",
  "出发时间改到早上 9 点",
];

Page({
  data: {
    tripId: "",
    missing: false,
    leftTab: "chat",
    trip: null,
    title: "",
    summaryText: "",
    companionText: "",
    intensityText: "",
    preferenceText: "",
    budgetText: "",
    selfDriveText: "",
    messages: [],
    input: "",
    pending: false,
    quickPrompts: quickPrompts,
    form: {},
    errors: [],
    nodeCount: 0,
  },
  onLoad(query) {
    const tripId = query.id || "";
    this.setData({ tripId: tripId });
    this.load(tripId);
  },
  onShow() {
    if (this.data.tripId) this.load(this.data.tripId);
  },
  load(tripId) {
    const trip = getTrip(tripId);
    if (!trip) {
      this.setData({ missing: true, trip: null });
      return;
    }
    this.setData({
      missing: false,
      trip: trip,
      title: trip.title,
      summaryText: trip.request.destination + " · " + trip.request.days + " 天",
      companionText: companionLabels[trip.request.companionType],
      intensityText: intensityLabels[trip.request.intensity],
      preferenceText: trip.request.preferences
        .map(function (p) { return preferenceLabels[p]; })
        .join("、"),
      budgetText: formatCurrency(trip.request.budgetPerPerson),
      selfDriveText: trip.request.selfDrive ? "是" : "否",
      messages: trip.messages.map(function (m) {
        return Object.assign({}, m, { isUser: m.role === "user" });
      }),
      form: Object.assign({}, trip.request),
      nodeCount: trip.days.reduce(function (n, d) { return n + d.nodes.length; }, 0),
    });
  },
  switchTab(e) {
    this.setData({ leftTab: e.currentTarget.dataset.tab, errors: [] });
  },
  onInput(e) {
    this.setData({ input: e.detail.value });
  },
  sendPrompt(e) {
    this.send(e.currentTarget.dataset.text);
  },
  sendInput() {
    this.send(this.data.input);
  },
  send(text) {
    const content = (text || "").trim();
    if (!content || this.data.pending) return;
    const tripId = this.data.tripId;
    const that = this;
    this.setData({ pending: true, input: "" });
    appendMessage(tripId, { role: "user", content: content });
    this.load(tripId);
    setTimeout(function () {
      appendMessage(tripId, { role: "assistant", content: mockAssistantReply(content) });
      that.setData({ pending: false });
      that.load(tripId);
    }, 500);
  },
  onFormChange(e) {
    this.setData({ form: e.detail.value });
  },
  validate(form) {
    const errors = [];
    if (!form.destination || !String(form.destination).trim()) errors.push("请填写目的地");
    if (!form.startDate) errors.push("请选择出行日期");
    if (!form.days || Number(form.days) < 1) errors.push("旅行天数至少为 1");
    if (!form.travelers || Number(form.travelers) < 1) errors.push("人数至少为 1");
    if (!form.budgetPerPerson || Number(form.budgetPerPerson) <= 0) errors.push("请填写人均预算");
    if (!form.preferences || !form.preferences.length) errors.push("请至少选择一个旅行偏好");
    return errors;
  },
  onSaveAdjust() {
    const form = this.data.form;
    const errors = this.validate(form);
    this.setData({ errors: errors });
    if (errors.length) return;
    const request = {
      destination: String(form.destination).trim(),
      startDate: String(form.startDate),
      days: Number(form.days),
      travelers: Number(form.travelers),
      budgetPerPerson: Number(form.budgetPerPerson),
      companionType: form.companionType,
      preferences: form.preferences,
      intensity: form.intensity,
      selfDrive: Boolean(form.selfDrive),
      specialRequests: String(form.specialRequests || "").trim() || undefined,
      wakeUpTime: String(form.wakeUpTime || "08:00"),
    };
    wx.showLoading({ title: "保存中…" });
    updateTripRequest(this.data.tripId, request);
    wx.hideLoading();
    wx.showToast({ title: "已重新生成", icon: "success" });
    this.setData({ leftTab: "chat" });
    this.load(this.data.tripId);
  },
  onCancelAdjust() {
    this.setData({ leftTab: "chat", errors: [] });
    if (this.data.trip) {
      this.setData({ form: Object.assign({}, this.data.trip.request) });
    }
  },
  onRegenerate() {
    regenerateTrip(this.data.tripId);
    wx.showToast({ title: "已重新生成", icon: "success" });
    this.load(this.data.tripId);
  },
  goDetail() {
    wx.navigateTo({ url: "/pages/detail/detail?id=" + this.data.tripId });
  },
  goBudget() {
    wx.navigateTo({ url: "/pages/budget/budget?id=" + this.data.tripId });
  },
  goCreate() {
    wx.switchTab({ url: "/pages/create/create" });
  },
});
