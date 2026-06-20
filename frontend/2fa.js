// 2FA SERVICE CLASS - HANDLES ALL 2FA OPERATIONS
class TwoFAService {
    constructor(authService) {
        this.authService = authService;
    }

    // INITIATE 2FA SETUP
    /*async enable2FA(password) {
        try {
            console.log('🔄 Starting 2FA setup...');
            
            const response = await this.authService.request('/auth/enable-2fa', {
                method: 'POST',
                body: JSON.stringify({ password })
            });

            console.log('✅ 2FA setup initiated');
            return response;
            
        } catch (error) {
            console.error('❌ 2FA setup failed:', error);
            throw new Error('2FA setup failed: ' + error.message);
        }
    }*/

    // VERIFY 2FA SETUP WITH CODE
    async verify2FASetup(code) {
        try {
            console.log('🔄 Verifying 2FA setup...');
            
            const response = await this.authService.request('/auth/verify-2fa-setup', {
                method: 'POST',
                body: JSON.stringify({ code })
            });

            console.log('✅ 2FA setup verified');
            return response;
            
        } catch (error) {
            console.error('❌ 2FA setup verification failed:', error);
            throw new Error('2FA setup verification failed: ' + error.message);
        }
    }

    // VERIFY 2FA CODE DURING LOGIN
    async verify2FALogin(code) {
        try {
            console.log('🔄 Verifying 2FA code for login...');
            
            const response = await this.authService.request('/auth/verify-2fa', {
                method: 'POST',
                body: JSON.stringify({ code })
            });

            console.log('✅ 2FA login verification successful');
            return response;
            
        } catch (error) {
            console.error('❌ 2FA verification failed:', error);
            throw new Error('2FA verification failed: ' + error.message);
        }
    }

    // DISABLE 2FA
    /*async disable2FA(password) {
        try {
            console.log('🔄 Disabling 2FA...');
            
            const response = await this.authService.request('/auth/disable-2fa', {
                method: 'POST',
                body: JSON.stringify({ password })
            });

            console.log('✅ 2FA disabled');
            return response;
            
        } catch (error) {
            console.error('❌ 2FA disable failed:', error);
            throw new Error('2FA disable failed: ' + error.message);
        }
    }*/

    // CHECK IF CURRENT USER HAS 2FA ENABLED
    async get2FAStatus() {
        try {
            // This would typically come from user profile endpoint
            // For now, we'll check if we can access protected routes without 2FA verification
            const userData = await this.authService.getCurrentUser();
            return userData.is_2fa_verified !== undefined;
        } catch (error) {
            console.log('2FA status check:', error.message);
            return false;
        }
    }
}