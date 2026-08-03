const {
  companionLabels,
  formatCurrency,
  intensityLabels,
  preferenceLabels,
} = require("../../utils/labels");
const { getTrip } = require("../../utils/store");

Page({
  data: {
    tripId: "",
    trip: null,
    missing: false,
  },
  onLoad(query) {
    const tripId = query.id || "";
    this.setData({ tripId: tripId });
    this.loadTrip(tripId);
  },
  onShow() {
    if (this.data.tripId) this.loadTrip(this.data.tripId);
  },
  loadTrip(tripId) {
    const trip = getTrip(tripId);
    if (!trip) {
      this.setData({ missing: true, trip: null });
      return;
    }
    this.setData({
      missing: false,
      trip: Object.assign({}, trip, {
        companionText: companionLabels[trip.request.companionType],
        intensityText: intensityLabels[trip.request.intensity],
        preferenceText: trip.request.preferences
          .map(function (p) { return preferenceLabels[p]; })
          .join("、"),
        budgetText:
          formatCurrency(trip.budget.estimatedTotal) +
          " / 预算 " +
          formatCurrency(trip.budget.totalBudget),
      }),
    });
  },
  goPlan() {
    wx.navigateTo({ url: "/pages/plan/plan?id=" + this.data.tripId });
  },
  goBudget() {
    wx.navigateTo({ url: "/pages/budget/budget?id=" + this.data.tripId });
  },
  goChecklist() {
    wx.navigateTo({ url: "/pages/checklist/checklist?id=" + this.data.tripId });
  },
  goCreate() {
    wx.switchTab({ url: "/pages/create/create" });
  },
});
