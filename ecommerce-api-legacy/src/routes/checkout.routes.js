const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function checkoutRoutes(checkoutController) {
    const router = Router();
    router.post('/checkout', asyncHandler(checkoutController));
    return router;
}

module.exports = checkoutRoutes;
