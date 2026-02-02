module.exports = {
    apps: [
        {
            name: 'voice-journal-bot',
            script: 'python',
            args: '-m bot.main',
            cwd: '/home/your-user/orchids-voice-journal-app',
            interpreter: 'none',
            instances: 1,
            autorestart: true,
            watch: false,
            max_memory_restart: '500M',
            env: {
                PYTHONUNBUFFERED: '1',
                // Environment variables will be loaded from .env file
            },
            error_file: './logs/pm2-error.log',
            out_file: './logs/pm2-out.log',
            log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
            merge_logs: true,
            kill_timeout: 5000,
        }
    ]
};
