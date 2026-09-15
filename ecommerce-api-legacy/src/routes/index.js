const { Router } = require('express');
const checkoutRoutes = require('./checkout.routes');
const financialReportRoutes = require('./financialReport.routes');
const usersRoutes = require('./users.routes');

function buildApiRouter({ checkoutController, financialReportController, userController }) {
    const router = Router();
    router.use(checkoutRoutes(checkoutController));
    router.use(financialReportRoutes(financialReportController));
    router.use(usersRoutes(userController));
    return router;
}

module.exports = buildApiRouter;
