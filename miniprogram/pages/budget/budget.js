const { budgetCategoryLabels, formatCurrency } = require("../../utils/labels");
const { getTrip } = require("../../utils/store");

Page({
  data: {
    tripId: "",
    missing: false,
    title: "",
    totalBudget: "",
    estimatedTotal: "",
    remaining: "",
    items: [],
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
      this.setData({ missing: true });
      return;
    }
    const breakdown = trip.budget.breakdown;
    const items = Object.keys(breakdown).map(function (key) {
      const value = breakdown[key];
      const percent = trip.budget.estimatedTotal
        ? Math.round((value / trip.budget.estimatedTotal) * 100)
        : 0;
      return {
        key: key,
        label: budgetCategoryLabels[key],
        value: formatCurrency(value),
        percent: percent,
      };
    });
    this.setData({
      missing: false,
      title: trip.title,
      totalBudget: formatCurrency(trip.budget.totalBudget),
      estimatedTotal: formatCurrency(trip.budget.estimatedTotal),
      remaining: formatCurrency(trip.budget.remaining),
      items: items,
    });
  },
  goDetail() {
    const id = this.data.tripId;
    wx.navigateBack({
      fail: function () {
        wx.redirectTo({ url: "/pages/detail/detail?id=" + id });
      },
    });
  },
  goPlan() {
    wx.navigateTo({ url: "/pages/plan/plan?id=" + this.data.tripId });
  },
});
