function makeFinancialReportController({ reportModel }) {
    return async function getFinancialReport(req, res) {
        const report = await reportModel.financialSummary();
        res.json(report);
    };
}

module.exports = makeFinancialReportController;
