class App {
    // constructor for enhanced 2fa flow
    constructor() {
        this.auth = new AuthService();
        this.twoFA = new TwoFAService(this.auth); // Enhanced: INITIALIZE 2FA SERVICE
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthStatus();
        // enhanced 
        this.check2FAStatus(); // NEW: CHECK 2FA STATUS ON LOAD
        
        // Auto-run debug on startup for development
        setTimeout(() => this.debugAuth(), 1000);
        /*
        // html elements do not exist when js runs
        // handle document.getElementById(...) is null
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.bindEvents();
                this.checkAuthStatus();
            });
        } else {
            this.bindEvents();
            this.checkAuthStatus();
        }*/
    }

    bindEvents() {
        // existing normal flow
        //  note - adjusted to add  DEBUG event bindings

        // added to handle document.getElementById(...) is null
        // Add null checks for all elements
        const loginForm = document.getElementById('login-form');
        const signupForm = document.getElementById('signup-form');

        const fetchUserBtn = document.getElementById('fetch-user-btn');
        const refreshTokenBtn = document.getElementById('refresh-token-btn');
        const logoutBtn = document.getElementById('logout-btn');
        
        const tabButtons = document.querySelectorAll('.tab-btn');

        if (!loginForm || !signupForm) {
            console.error('Forms not found');
            return;
        }

         // Tab switching
        tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Form submissions
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        signupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSignup();
        });

        //existing normal flow
        // Protected section buttons
        if (fetchUserBtn) {
            fetchUserBtn.addEventListener('click', () => {
                this.fetchUserData();
            });
        }

        if (refreshTokenBtn) {
            refreshTokenBtn.addEventListener('click', () => {
                this.refreshToken();
            });
        }

        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.handleLogout();
            });
        }

        // existing normal flow
        // DEBUG EVENT BINDINGS
        const debugAuthBtn = document.getElementById('debug-auth-btn');
        const testEndpointsBtn = document.getElementById('test-endpoints-btn');
        const debugLogoutBtn = document.getElementById('debug-logout-btn');
        // FORCE REFRESH BUTTON FOR DEBUGGING PROPERTIES
        const forceRefreshBtn = document.getElementById('force-refresh-btn'); 
        
        if (debugAuthBtn) {
            debugAuthBtn.addEventListener('click', () => this.debugAuth());
        }
        
        if (testEndpointsBtn) {
            testEndpointsBtn.addEventListener('click', () => this.testEndpoints());
        }
        
        if (debugLogoutBtn) {
            debugLogoutBtn.addEventListener('click', () => this.debugLogout());
        }

        // FORCE Refresh Button Handler
        if (forceRefreshBtn) {
            forceRefreshBtn.addEventListener('click', () => this.forceRefresh());
        }
        // --- END DEBUG EVENT BINDINGS

        //enhanced flow
        // 2FA BUTTON EVENT BINDINGS
        this.bind2FAEvents();
        
    }

    // Enhanced flow: BIND 2FA-SPECIFIC EVENTS
    bind2FAEvents() {
        //// removed ENABLE 2FA BUTTON - ALWAYS ENABLED FOR CURRENT IMPLEMENTATION
        //const enable2FABtn = document.getElementById('enable-2fa-btn');
        
        //// removed DISABLE 2FA BUTTON - ALWAYS ENABLED FOR CURRENT IMPLEMENTATION
        //const disable2FABtn = document.getElementById('disable-2fa-btn');
        
        const verify2FASetupBtn = document.getElementById('verify-2fa-setup-btn');
        const verify2FALoginBtn = document.getElementById('verify-2fa-login-btn');
        const verify2FASignupBtn = document.getElementById('verify-2fa-signup-btn');
        ///// deprecated
        ////const cancel2FABtn = document.getElementById('cancel-2fa-btn');

        //// removed DISABLE 2FA BUTTON - ALWAYS ENABLED
        //if (enable2FABtn) {
        //    enable2FABtn.addEventListener('click', () => this.enable2FA());
        //}

        //// removed DISABLE 2FA BUTTON - ALWAYS ENABLED
        //if (disable2FABtn) {
        //    disable2FABtn.addEventListener('click', () => this.disable2FA());
        //}

        const cancel2FALoginBtn = document.getElementById('cancel-2fa-login-btn');
        const cancel2FASignupBtn = document.getElementById('cancel-2fa-signup-btn');

        if (cancel2FALoginBtn) {
            cancel2FALoginBtn.addEventListener('click', () => this.cancel2FA());
        }

        if (cancel2FASignupBtn) {
            cancel2FASignupBtn.addEventListener('click', () => this.cancel2FA());
        }

        if (verify2FALoginBtn) {
            verify2FALoginBtn.addEventListener('click', () => this.verify2FALogin());
        }

        if (verify2FASignupBtn) {
            verify2FASignupBtn.addEventListener('click', () => this.verify2FASignup());
        }

        ///// deprecated
        ////if (cancel2FABtn) {
        ////    cancel2FABtn.addEventListener('click', () => this.cancel2FA());
        ////}

        if (verify2FASetupBtn) {
            verify2FASetupBtn.addEventListener('click', () => this.verify2FASetup());
        }

        
    }

    // normal flow
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    // enhanced flow
    async handleLogin() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const messageEl = document.getElementById('login-message');

        try {
            this.showMessage(messageEl, 'Logging in...', 'info');

            // enhanced: 2FA-AWARE LOGIN
            const result = await this.auth.login(email, password);

            if (result.requires2FA){
                // SHOW 2FA VERIFICATION MODAL
                this.showMessage(messageEl, '2FA verification required', 'info');
                this.show2FALoginModal();

            }else{
                this.showMessage(messageEl, 'Login successful!', 'success');
                this.checkAuthStatus();
            
                // Force check auth status immediately
                setTimeout(() => {
                    this.checkAuthStatus();
                }, 100);

                // Clear form
                document.getElementById('login-form').reset();
            }
            
        } catch (error) {
            this.showMessage(messageEl, error.message, 'error');
        }
    }


    // enhanced flow: 2FA LOGIN VERIFICATION
    async verify2FALogin() {
        const code = document.getElementById('login-2fa-code').value;
        const messageEl = document.getElementById('login-2fa-message');

        if (!code || code.length !== 6) {
            this.showMessage(messageEl, 'Please enter a valid 6-digit code', 'error');
            return;
        }

        try {
            this.showMessage(messageEl, 'Verifying 2FA code...', 'info');
            
            // !!!!!!!!! THIS CALLS THE LOGIN 2FA VERIFICATION ENDPOINT !!!!!!!!!
            await this.auth.complete2FALogin(code);
            
            this.showMessage(messageEl, '2FA verification successful!', 'success');
            this.hide2FAModal();
            this.checkAuthStatus();
            
            // CLEAR THE FORM
            document.getElementById('login-2fa-code').value = '';
            
        } catch (error) {
            this.showMessage(messageEl, error.message, 'error');
        }
    }

    // REMOVED ENABLE 2FA METHOD - ALWAYS ENABLED
    // enhanced flow: ENABLE 2FA
    /* async enable2FA() {
        const password = document.getElementById('enable-2fa-password').value;
        const messageEl = document.getElementById('enable-2fa-message');

        if (!password) {
            this.showMessage(messageEl, 'Please enter your password', 'error');
            return;
        }

        try {
            this.showMessage(messageEl, 'Setting up 2FA...', 'info');
            
            const result = await this.twoFA.enable2FA(password);
            
            // SHOW QR CODE AND MANUAL ENTRY OPTION
            this.show2FASetupModal(result.qr_code, result.manual_code);
            this.showMessage(messageEl, '2FA setup initiated - scan the QR code', 'success');
            
            // CLEAR PASSWORD FIELD
            document.getElementById('enable-2fa-password').value = '';
            
        } catch (error) {
            this.showMessage(messageEl, error.message, 'error');
        }
    } */

    //required for login VERIFY 2FA SETUP METHOD
    // enhanced flow: VERIFY 2FA SETUP
    async verify2FASetup() {
        const code = document.getElementById('setup-2fa-code').value;
        const messageEl = document.getElementById('setup-2fa-message');

        if (!code || code.length !== 6) {
            this.showMessage(messageEl, 'Please enter a valid 6-digit code', 'error');
            return;
        }

        try {
            this.showMessage(messageEl, 'Verifying setup code...', 'info');
            
            const result = await this.twoFA.verify2FASetup(code);
            
            this.showMessage(messageEl, '2FA enabled successfully!', 'success');
            this.hide2FAModal();
            this.update2FAStatus(true);
            
            // CLEAR THE FORM
            document.getElementById('setup-2fa-code').value = '';
            
        } catch (error) {
            this.showMessage(messageEl, error.message, 'error');
        }
    }

    // REMOVED DISABLE 2FA METHOD - ALWAYS ENABLED
    // enhanced flow: DISABLE 2FA
    /* async disable2FA() {
        const password = document.getElementById('disable-2fa-password').value;
        const messageEl = document.getElementById('disable-2fa-message');

        if (!password) {
            this.showMessage(messageEl, 'Please enter your password', 'error');
            return;
        }

        try {
            this.showMessage(messageEl, 'Disabling 2FA...', 'info');
            
            await this.twoFA.disable2FA(password);
            
            this.showMessage(messageEl, '2FA disabled successfully!', 'success');
            this.update2FAStatus(false);
            
            // CLEAR PASSWORD FIELD
            document.getElementById('disable-2fa-password').value = '';
            
        } catch (error) {
            this.showMessage(messageEl, error.message, 'error');
        }
    } */

    // cancel is user opting out of prerequired 2fa login    
    // enhanced flow: CANCEL 2FA OPERATION
    cancel2FA() {
        this.hide2FAModal();
        this.auth.clear2FAState(); // CLEAR ANY PENDING 2FA STATE
    }

    // unREMOVED SHOW 2FA SETUP MODAL for signup (2fa signup as well)
    // enhanced flow: SHOW 2FA SETUP MODAL
    show2FASetupModal(qrCode, manualCode) {
        const modal = document.getElementById('2fa-setup-modal');
        const qrCodeImg = document.getElementById('2fa-qr-code');
        const manualCodeEl = document.getElementById('2fa-manual-code');

        if (qrCodeImg) qrCodeImg.src = qrCode;
        if (manualCodeEl) manualCodeEl.textContent = manualCode;
        if (modal) modal.style.display = 'block';

        // SWITCH TO SETUP VERIFICATION TAB
        this.switch2FATab('setup');
    }

    // enhanced flow: SHOW 2FA LOGIN MODAL
    show2FALoginModal() {
        const modal = document.getElementById('2fa-login-modal');
        const userEmail = document.getElementById('2fa-login-email');
        
        if (userEmail) userEmail.textContent = this.auth.getPendingEmail();
        if (modal) modal.style.display = 'block';
    }


    // !!!!!!!!! Enhanced for signup 2fa !!!!!!!!!
    hide2FAModal() {
        const loginModal = document.getElementById('2fa-login-modal');
        const signupModal = document.getElementById('2fa-signup-modal'); // !!!!!!!!! ADDED SIGNUP MODAL !!!!!!!!!
    
        if (loginModal) loginModal.style.display = 'none';
        if (signupModal) signupModal.style.display = 'none'; // !!!!!!!!! HIDE SIGNUP MODAL !!!!!!!!!
    }

    
    // enhanced flow: SWITCH 2FA TABS
     switch2FATab(tabName) {
        // UPDATE TAB BUTTONS
        document.querySelectorAll('.2fa-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-2fa-tab="${tabName}"]`).classList.add('active');

        // UPDATE TAB CONTENT
        document.querySelectorAll('.2fa-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`2fa-${tabName}-tab`).classList.add('active');
    }
    

    // UPDATED: UPDATE 2FA STATUS DISPLAY - ALWAYS SHOW ENABLED
    // NEW: UPDATE 2FA STATUS DISPLAY
    update2FAStatus(isEnabled) {
        const statusEl = document.getElementById('2fa-status');
        const enableSection = document.getElementById('2fa-enable-section');
        const disableSection = document.getElementById('2fa-disable-section');

        if (statusEl) {
            //// for testing implementation for signup not needing 2fa
            //// now deprecated
            //statusEl.textContent = '🟢 Always Enabled';
            //statusEl.className = '2fa-status enabled';
            statusEl.textContent = isEnabled ? '🟢 Enabled' : '🔴 Disabled';
            statusEl.className = isEnabled ? '2fa-status enabled' : '2fa-status disabled';
        }
        //// do w/o enableSection and disableSection 
        /*
        if (enableSection) {
            enableSection.style.display = 'none'; // HIDE ENABLE SECTION
        }

        if (disableSection) {
            disableSection.style.display = 'none'; // HIDE DISABLE SECTION
        }*/

        /*if (enableSection) {
            enableSection.style.display = isEnabled ? 'none' : 'block';
        }

        if (disableSection) {
            disableSection.style.display = isEnabled ? 'block' : 'none';
        }*/
    }

    // Enhanced: CHECK 2FA STATUS - ALWAYS ENABLED
    async check2FAStatus() {
        // This would typically come from a user profile endpoint
        // For now, we'll simulate based on authentication
        if (this.auth.isAuthenticated()) {
            // In a real app, you'd fetch this from /auth/me or similar
            const has2FA = await this.twoFA.get2FAStatus();
            this.update2FAStatus(has2FA);
        }
        //// deprecatd implementation, used for testing for signup w/o 2fa
        //// Since 2FA is always enabled, always update to show it as enabled
        /*if (this.auth.isAuthenticated()) {
            this.update2FAStatus(true); // Always show as enabled
        }*/
    }


    async handleSignup() {
        const formData = {
            first_name: document.getElementById('signup-firstname').value,
            last_name: document.getElementById('signup-lastname').value,
            username: document.getElementById('signup-username').value,
            email: document.getElementById('signup-email').value,
            password: document.getElementById('signup-password').value,
        };

        const messageEl = document.getElementById('signup-message');

        try {
            this.showMessage(messageEl, 'Creating account...', 'info');
            await this.auth.signup(formData);
            // !!!!!!!!! SIGNUP ALWAYS REQUIRES 2FA VERIFICATION NOW !!!!!!!!!
            this.showMessage(messageEl, result.message, 'info');
            // !!!!!!!!! SHOW 2FA VERIFICATION MODAL FOR SIGNUP !!!!!!!!!
            this.show2FASignupModal();

            //// deprecated implementation w/o 2fa @ signup
            //this.showMessage(messageEl, 'Account created successfully! Please login.', 'success');
            //// Switch to login tab and pre-fill email
            //this.switchTab('login');
            //document.getElementById('login-email').value = formData.email;
            //// Clear form
            //document.getElementById('signup-form').reset();
        } catch (error) {
            this.showMessage(messageEl, error.message, 'error');
        }
    }

    // !!!!!!!!!  SHOW 2FA SIGNUP MODAL !!!!!!!!! 
    show2FASignupModal() {
        const modal = document.getElementById('2fa-signup-modal');
        if (modal) modal.style.display = 'block';
    }

    // !!!!!!!!! NEW METHOD: VERIFY 2FA CODE DURING SIGNUP !!!!!!!!!
    async verify2FASignup() {
        const code = document.getElementById('signup-2fa-code').value;
        const messageEl = document.getElementById('signup-2fa-message');

        if (!code || code.length !== 6) {
            this.showMessage(messageEl, 'Please enter a valid 6-digit code', 'error');
            return;
        }

        try {
            this.showMessage(messageEl, 'Verifying 2FA code...', 'info');
            
            // !!!!!!!!! USE THE TEMP TOKEN FROM SIGNUP FOR VERIFICATION !!!!!!!!!
            const originalToken = this.auth.accessToken;
            this.auth.accessToken = this.auth.tempToken;
            
            const response = await this.auth.request('/auth/verify-2fa-setup', {
                method: 'POST',
                body: JSON.stringify({ code })
            });

            // !!!!!!!!! RESTORE ORIGINAL TOKEN AND SET NEW FULL TOKENS !!!!!!!!!
            this.auth.accessToken = originalToken;
            this.auth.setTokens(response.access_token, response.refresh_token);
            this.auth.setUserEmail(response.user.email);
            this.auth.clear2FAState(); // CLEAR 2FA STATE AFTER SUCCESS
            
            this.showMessage(messageEl, '2FA verification successful! Account fully created.', 'success');
            this.hide2FAModal();
            this.checkAuthStatus();
            
            // CLEAR THE FORM
            document.getElementById('signup-2fa-code').value = '';
            
        } catch (error) {
            this.showMessage(messageEl, error.message, 'error');
        }
    }



    async fetchUserData() {
        const userDataEl = document.getElementById('user-data');

        try {
            userDataEl.textContent = 'Loading...';
            console.log('🔄 Fetching user data...');
            const data = await this.auth.getCurrentUser();
            userDataEl.textContent = JSON.stringify(data, null, 2);
            userDataEl.style.color = 'green';
            console.log('✅ User data fetched successfully');
            // Update debug display after successful fetch
            this.updateDebugDisplay();
        } catch (error) {
            userDataEl.textContent = `Error: ${error.message}`;
            userDataEl.style.color = 'red';
            console.error('❌ Failed to fetch user data:', error);
        }
    }



    // IMPORTANT! 
    // This is the manual (button) refresh token functionality
    // Note: The automated one is handled within auth.getCurrentUser()
    // both call auth.refreshAcessToken()
    // User can get a new access_token regardless of expiry
    
    // commented out implementation: doesn't show part of the refreshed token
    // refreshToken() implementation not commented out is used for testing purposes
    
    /*async refreshToken() {
        try {
            await this.auth.refreshAccessToken();
            this.showMessage(document.getElementById('user-data'), 'Token refreshed successfully!', 'success');
        } catch (error) {
            this.showMessage(document.getElementById('user-data'), `Refresh failed: ${error.message}`, 'error');
        }
    }*/

    // IMPORTANT! 
    // This is the manual (button) refresh token functionality
    // Note: The automated one is handled within auth.getCurrentUser()
    // both call auth.refreshAcessToken()
    // User can get a new access_token regardless of expiry
    //manual jwt token resfresh used as well

    //uses: 
    //this.auth.refreshAccessToken();
    async refreshToken() {
        // Update the message with the new token info.
        // For debugging purposes, a part of the fresh token
        // is displayed.
        const userDataEl = document.getElementById('user-data');
        try {
            ////const userDataEl = document.getElementById('user-data');
            //log state change
            console.log('🔄 Manual token refresh initiated...');

            //log the old state for comparison after the refresh
            if (userDataEl) {
                userDataEl.textContent = 'Refreshing token...';
                userDataEl.style.color = 'blue';
            }
        
            // Store old token for detailed comparison
            const oldToken = this.auth.accessToken;
            // what if there is no previous state?
            const oldTokenLast50 = oldToken ? oldToken.slice(-50) : 'No previous token';
        
            console.log('📊 Token comparison data:');
            console.log('   Old token length:', oldToken?.length);
            console.log('   Old token last 50:', oldTokenLast50);

            // Actual function call
            const refreshData = await this.auth.refreshAccessToken();
            const newToken = refreshData.access_token;
            const newTokenLast50 = newToken.slice(-50);
        
            console.log('   New token length:', newToken.length);
            console.log('   New token last 50:', newTokenLast50);
            console.log('   Tokens identical:', oldToken === newToken);
            console.log('   Last 50 chars identical:', oldTokenLast50 === newTokenLast50);


            //// Begin implementation of  detailed comparison message
            const tokensAreDifferent = oldToken !== newToken;
            const changeEmoji = tokensAreDifferent ? '✅' : '⚠️';
            const changeMessage = tokensAreDifferent ? 'DIFFERENT' : 'SAME';
            
            const message = `${changeEmoji} TOKEN REFRESH COMPLETE\n\n` +
                        `Token Change: ${changeMessage}\n` +
                        `Old Token (last 50): ${oldTokenLast50}\n` +
                        `New Token (last 50): ${newTokenLast50}\n` +
                        `Full Token Match: ${!tokensAreDifferent ? 'YES ⚠️' : 'NO ✅'}\n\n` +
                        `Token refresh was successful!`;
            
            if (userDataEl) {
                userDataEl.textContent = message;
                userDataEl.style.color = tokensAreDifferent ? 'green' : 'orange';
            }
            
            console.log('✅ Manual token refresh completed with change detection');
            //// End implementation of  detailed comparison message
        
            this.updateDebugDisplay();
        } catch (error) {
            console.error('❌ Manual token refresh failed:', error);
            //// const userDataEl = document.getElementById('user-data');
            if (userDataEl) {
                userDataEl.textContent = `❌ REFRESH FAILED:\n${error.message}`;
                userDataEl.style.color = 'red';
            }
            
            /*this.showMessage(document.getElementById('user-data'), 
                `Refresh failed: ${error.message}`, 'error');*/
        }
    }

    handleLogout() {
        this.auth.logout();
        this.checkAuthStatus();
        this.switchTab('login');
        
        // Clear any displayed user data
        document.getElementById('user-data').textContent = '';
    }

    checkAuthStatus() {
        const authSection = document.querySelector('.auth-section');
        const protectedSection = document.getElementById('protected-section');
        const logoutBtn = document.getElementById('logout-btn');
        const userEmailEl = document.getElementById('user-email');

        console.log('Elements found:', {
            authSection: !!authSection,
            protectedSection: !!protectedSection, 
            logoutBtn: !!logoutBtn,
            userEmailEl: !!userEmailEl
        });

        console.log('isAuthenticated:', this.auth.isAuthenticated());
        console.log('User email:', this.auth.getUserEmail());

        // Add null checks for all elements
        // checkAuthStatus would be otherwise trying to access elements
        // that do not exist yet
        if (!authSection || !protectedSection || !logoutBtn || !userEmailEl) {
            console.log('Auth elements not found yet');
            return;
        }

        if (this.auth.isAuthenticated()) {
            // User is logged in
            // log for debugging purposes
            console.log('User is authenticated - showing protected area');
            authSection.style.display = 'none';
            protectedSection.style.display = 'block';
            logoutBtn.style.display = 'block';
            userEmailEl.textContent = this.auth.getUserEmail();

            // enhanced workflow
            this.check2FAStatus();
        } else {
            // User is not logged in
            // log for debugging purposes
            console.log('User is not authenticated - showing login forms');
            authSection.style.display = 'block';
            protectedSection.style.display = 'none';
            logoutBtn.style.display = 'none';
            userEmailEl.textContent = '';
        }
    }

    showMessage(element, message, type) {
        element.textContent = message;
        element.className = `message ${type}`;
        element.style.display = 'block';

        if (type !== 'info') {
            setTimeout(() => {
                element.style.display = 'none';
            }, 5000);
        }
    }


    // The following section is meant to be utilized for 
    // testing purposes only, comment out as necessary

    // === DEBUG METHODS ===
    
    /**
     * Comprehensive authentication debug information
     */
    debugAuth() {
        console.log('🔍 === AUTHENTICATION DEBUG REPORT ===');

        // 1.  Token analysis
        console.log('🔐 TOKEN ANALYSIS:');
        console.log('   Access Token Present:', this.auth.accessToken ? '✅ Yes' : '❌ No');
        console.log('   Refresh Token Present:', this.auth.refreshToken ? '✅ Yes' : '❌ No');
        
        if (this.auth.accessToken) {
            try {
                const tokenData = JSON.parse(atob(this.auth.accessToken.split('.')[1]));
                const expiryTime = new Date(tokenData.exp * 1000);
                const timeUntilExpiry = expiryTime - new Date();
                const minutesUntilExpiry = Math.floor(timeUntilExpiry / 1000 / 60);
                
                console.log('   Token Expires:', expiryTime.toLocaleString());
                console.log('   Time Until Expiry:', minutesUntilExpiry + ' minutes');
                console.log('   Token User:', tokenData.user);
                
                // Check if token is about to expire
                if (minutesUntilExpiry < 5) {
                    console.log('   ⚠️ Token will expire soon!');
                }
            } catch (e) {
                console.log('   Token Parse Error:', e.message);
            }
        }
        
        // 2. Local Storage Analysis
        console.log('📦 LOCAL STORAGE:');
        console.log('   Access Token:', this.auth.accessToken ? '✅ Present' : '❌ Missing');
        console.log('   Refresh Token:', this.auth.refreshToken ? '✅ Present' : '❌ Missing');
        console.log('   User Email:', this.auth.userEmail || '❌ Missing');
        // enhanced view for local storage
        console.log('   2FA Pending:', this.auth.pending2FA ? '✅ Yes' : '❌ No');
        console.log('   Temp Token:', this.auth.tempToken ? '✅ Present' : '❌ Missing');
        
        if (this.auth.accessToken) {
            try {
                const tokenData = JSON.parse(atob(this.auth.accessToken.split('.')[1]));
                const expiryTime = new Date(tokenData.exp * 1000);
                const timeUntilExpiry = expiryTime - new Date();
                console.log('   Token Expires:', expiryTime.toLocaleString());
                console.log('   Time Until Expiry:', Math.floor(timeUntilExpiry / 1000 / 60) + ' minutes');
            } catch (e) {
                console.log('   Token Parse Error:', e.message);
            }
        }
        
        // 3. DOM Elements Analysis
        console.log('🏗️ DOM ELEMENTS:');
        const authSection = document.querySelector('.auth-section');
        const protectedSection = document.getElementById('protected-section');
        const logoutBtn = document.getElementById('logout-btn');
        const userEmailEl = document.getElementById('user-email');
        
        console.log('   Auth Section:', authSection ? '✅ Found' : '❌ Missing');
        console.log('   Protected Section:', protectedSection ? '✅ Found' : '❌ Missing');
        console.log('   Logout Button:', logoutBtn ? '✅ Found' : '❌ Missing');
        console.log('   User Email Element:', userEmailEl ? '✅ Found' : '❌ Missing');
        
        // 4. Visibility States
        console.log('👀 VISIBILITY STATES:');
        if (authSection) {
            console.log('   Auth Section Display:', getComputedStyle(authSection).display);
        }
        if (protectedSection) {
            console.log('   Protected Section Display:', getComputedStyle(protectedSection).display);
        }
        if (logoutBtn) {
            console.log('   Logout Button Display:', getComputedStyle(logoutBtn).display);
        }
        
        // 5. Authentication State
        console.log('🔐 AUTH STATE:');
        console.log('   isAuthenticated():', this.auth.isAuthenticated());
        console.log('   User Email (Memory):', this.auth.getUserEmail());
        
        // 6. Current View Analysis
        console.log('📱 CURRENT VIEW:');
        const activeTab = document.querySelector('.tab-btn.active');
        console.log('   Active Tab:', activeTab ? activeTab.dataset.tab : 'None');
        
        console.log('========================================');
        
        // Update debug display if it exists
        this.updateDebugDisplay();
    }
    
    /**
     * Enhanced Force refresh token and update user data with even more detailed info
     */
    async forceRefresh() {
        const userDataEl = document.getElementById('user-data');
        
        try {
            console.log('🔄 FORCE REFRESH initiated...');
            
            if (userDataEl) {
                userDataEl.textContent = 'Force refreshing token...';
                userDataEl.style.color = 'purple';
            }
            // Previous token segment
            // Store old token for comparison
            const oldToken = this.auth.accessToken;
            // Store comprehensive old token data
            const oldTokenFirst30 = oldToken ? oldToken.slice(0, 30) : 'N/A';
            const oldTokenLast50 = oldToken ? oldToken.slice(-50) : 'N/A';
            const oldTokenLength = oldToken ? oldToken.length : 0;
            // Actualcall to .auth.refreshAccessToken()
            // Force token refresh
            const refreshData = await this.auth.refreshAccessToken();
            const newToken = refreshData.access_token;
            const newTokenFirst30 = newToken.slice(0, 30);
            const newTokenLast50 = newToken.slice(-50);

            
            // Detailed comparison
            const tokensAreDifferent = oldToken !== newToken;
            const changeEmoji = tokensAreDifferent ? '🎉' : '🔁';
            const changeMessage = tokensAreDifferent ? 'CHANGED SUCCESSFULLY' : 'REMAINED THE SAME';
            
            const message = `${changeEmoji} FORCE REFRESH RESULTS\n\n` +
                        `STATUS: ${changeMessage}\n\n` +
                        `COMPARISON:\n` +
                        `• Full Match: ${!tokensAreDifferent ? 'YES ⚠️' : 'NO ✅'}\n` +
                        `• Old Length: ${oldTokenLength} chars\n` +
                        `• New Length: ${newToken.length} chars\n\n` +
                        `TOKEN PREVIEWS:\n` +
                        `Old (first 30): ${oldTokenFirst30}...\n` +
                        `New (first 30): ${newTokenFirst30}...\n\n` +
                        `LAST 50 CHARACTERS:\n` +
                        `Old: ${oldTokenLast50}\n` +
                        `New: ${newTokenLast50}`;
            
            if (userDataEl) {
                userDataEl.textContent = message;
                userDataEl.style.color = tokensAreDifferent ? 'darkgreen' : 'darkorange';
                userDataEl.style.fontFamily = 'monospace';
                userDataEl.style.whiteSpace = 'pre-wrap';
            }
            
            console.log('✅ Force refresh completed with detailed analysis');
                
            // Update debug display
            this.updateDebugDisplay();
            
        } catch (error) {
            console.error('❌ Force refresh failed:', error);
        
            if (userDataEl) {
                userDataEl.textContent = `❌ FORCE REFRESH FAILED:\n${error.message}`;
                userDataEl.style.color = 'red';
            }
        }
    }

    /**
     * Enhanced auto-refresh handler for natural expiration
     */
    async handleAutoRefresh() {
        const userDataEl = document.getElementById('user-data');
        
        try {
            console.log('🔄 Auto-refresh triggered (token expired)');
            
            const oldToken = this.auth.accessToken;
            const oldTokenLast50 = oldToken ? oldToken.slice(-50) : 'No token';
            
            const refreshData = await this.auth.refreshAccessToken();
            const newToken = refreshData.access_token;
            const newTokenLast50 = newToken.slice(-50);
            
            const tokensAreDifferent = oldToken !== newToken;
            
            if (userDataEl && tokensAreDifferent) {
                const message = `🔄 AUTO-REFRESH (Token Expired)\n\n` +
                            `Token was automatically refreshed!\n` +
                            `Change Detected: ✅ YES\n\n` +
                            `Last 50 Characters:\n` +
                            `Old: ${oldTokenLast50}\n` +
                            `New: ${newTokenLast50}`;
                
                userDataEl.textContent = message;
                userDataEl.style.color = 'blue';
                userDataEl.style.fontFamily = 'monospace';
                userDataEl.style.whiteSpace = 'pre-wrap';
                
                // Auto-clear after 5 seconds
                setTimeout(() => {
                    if (userDataEl.textContent.includes('AUTO-REFRESH')) {
                        userDataEl.textContent = 'Click "Get My Profile" to test with new token';
                        userDataEl.style.color = 'black';
                    }
                }, 5000);
            }
            
        } catch (error) {
            console.error('❌ Auto-refresh failed:', error);
        }
    }

    /**
     * Update the debug info in the UI
     */
    updateDebugDisplay() {
        const debugInfoEl = document.getElementById('debug-info');
        if (!debugInfoEl) return;
        
        const authStatus = this.auth.isAuthenticated() ? '✅ AUTHENTICATED' : '❌ NOT AUTHENTICATED';
        const tokenStatus = this.auth.accessToken ? '✅ Present' : '❌ Missing';
        const elementsStatus = document.getElementById('protected-section') ? '✅ Found' : '❌ Missing';
        
        debugInfoEl.innerHTML = `
            <strong>Debug Info:</strong><br>
            Status: ${authStatus}<br>
            Token: ${tokenStatus}<br>
            Elements: ${elementsStatus}<br>
            User: ${this.auth.getUserEmail() || 'None'}
        `;
    }
    
    /**
     * Test API endpoints
     */
    async testEndpoints() {
        console.log('🚀 === TESTING API ENDPOINTS ===');
        
        try {
            // Test database connection
            const dbPing = await this.auth.request('/auth/debug/db-ping');
            console.log('✅ Database Ping:', dbPing.status);
            
            // Test protected route if authenticated
            if (this.auth.isAuthenticated()) {
                const userData = await this.auth.getCurrentUser();
                console.log('✅ Protected Route:', 'Access granted');
                console.log('   User Data:', userData);
            } else {
                console.log('⏸️ Protected Route:', 'Skipped (not authenticated)');
            }
            
            //enhanced for 2fa
            // TEST THE DEBUG CURRENT TOTP ENDPOINT
            try {
                const totpCode = await this.auth.request('/auth/debug/current-totp');
                console.log('✅ Current TOTP Code:', totpCode.current_code);
            } catch (totpError) {
                console.log('❌ Current TOTP endpoint error:', totpError.message);
            }

            console.log('================================');
        } catch (error) {
            console.log('❌ API Test Failed:', error.message);
        }
    }
    
    /**
     * Clear all authentication data
     */
    debugLogout() {
        console.log('🔄 Debug: Clearing all auth data');
        this.auth.logout();
        this.checkAuthStatus();
        this.debugAuth();
    }
   

}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new App();
});