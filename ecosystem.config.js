module.exports = {
    apps: [
        {
            name: 'voice-journal-bot',
            script: 'python',
            args: '-m bot.main',
            cwd: './',
            interpreter: 'none', // We use the python command from the environment
            instances: 1,
            autorestart: true,
            watch: false, // Don't watch files, we'll restart manually after updates
            max_memory_restart: '500M',
            env: {
                PYTHONUNBUFFERED: '1',
            },
        }
    ]
};
