const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdmin = require('../middlewares/requireAdmin');

function financialReportRoutes(financialReportController) {
    const router = Router();
    router.get('/admin/financial-report', requireAdmin, asyncHandler(financialReportController));
    return router;
}

module.exports = financialReportRoutes;
