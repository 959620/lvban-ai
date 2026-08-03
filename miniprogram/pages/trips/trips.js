const { formatCurrency, statusLabels } = require("../../utils/labels");
const { listSummaries } = require("../../utils/store");

Page({
  data: {
    trips: [],
  },
  onShow() {
    const summaries = listSummaries();
    this.setData({
      trips: summaries.map((t) => ({
        ...t,
        statusText: statusLabels[t.status],
        budgetText: formatCurrency(t.estimatedTotal),
      })),
    });
  },
  openTrip(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  },
  goCreate() {
    wx.switchTab({ url: "/pages/create/create" });
  },
});
