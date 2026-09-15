const express = require('express');
const settings = require('./config/settings');
const logger = require('./services/loggerService');
const { createConnection } = require('./db/connection');
const { createSchema } = require('./db/schema');
const { seed } = require('./db/seed');

const UserModel = require('./models/UserModel');
const CourseModel = require('./models/CourseModel');
const EnrollmentModel = require('./models/EnrollmentModel');
const PaymentModel = require('./models/PaymentModel');
const AuditLogModel = require('./models/AuditLogModel');
const ReportModel = require('./models/ReportModel');

const makeCheckoutController = require('./controllers/checkoutController');
const makeFinancialReportController = require('./controllers/financialReportController');
const makeUserController = require('./controllers/userController');

const buildApiRouter = require('./routes');
const { notFoundHandler, errorHandler } = require('./middlewares/errorHandler');

async function createApp() {
    const db = createConnection(':memory:');
    await createSchema(db);
    await seed(db);

    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);
    const reportModel = new ReportModel(db);

    const checkoutController = makeCheckoutController({
        db,
        userModel,
        courseModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
    });
    const financialReportController = makeFinancialReportController({ reportModel });
    const userController = makeUserController({ userModel });

    const app = express();
    app.use(express.json());
    app.use('/api', buildApiRouter({ checkoutController, financialReportController, userController }));
    app.use(notFoundHandler);
    app.use(errorHandler);

    return app;
}

async function main() {
    const app = await createApp();
    app.listen(settings.port, () => {
        logger.info('server.started', { port: settings.port });
    });
}

if (require.main === module) {
    main().catch((err) => {
        logger.error('server.boot_failed', { message: err.message });
        process.exit(1);
    });
}

module.exports = { createApp };
