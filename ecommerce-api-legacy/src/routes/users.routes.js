const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdmin = require('../middlewares/requireAdmin');

function usersRoutes(userController) {
    const router = Router();
    router.delete('/users/:id', requireAdmin, asyncHandler(userController.deleteUser));
    return router;
}

module.exports = usersRoutes;
