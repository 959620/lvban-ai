const { createTrip } = require("../../utils/store");

function today() {
  const d = new Date();
  const m = `${d.getMonth() + 1}`.padStart(2, "0");
  const day = `${d.getDate()}`.padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

Page({
  data: {
    form: {
      destination: "",
      startDate: today(),
      days: 3,
      travelers: 2,
      budgetPerPerson: 2000,
      companionType: "friends",
      preferences: [],
      intensity: "moderate",
      selfDrive: false,
      specialRequests: "",
      wakeUpTime: "08:00",
    },
    errors: [],
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
  onSubmit() {
    const form = this.data.form;
    const errors = this.validate(form);
    this.setData({ errors });
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

    wx.showLoading({ title: "生成中…" });
    const trip = createTrip(request);
    wx.hideLoading();
    wx.navigateTo({ url: `/pages/detail/detail?id=${trip.id}` });
  },
  goDemo() {
    wx.navigateTo({ url: "/pages/detail/detail?id=trip-dali-demo" });
  },
});
