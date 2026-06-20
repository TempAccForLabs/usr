class AuthService {
    constructor() {
        // base url to api calls to fastapi backend
        this.baseURL = ''; // Use same origin (works with Replit proxy)
        
        // in the current implementation, the tokens and mail are
        // kept in the local storage
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.userEmail = localStorage.getItem('user_email');

        // Added for 2fa: 2FA STATE TRACKING
        this.pending2FA = localStorage.getItem('pending_2fa') === 'true';
        this.tempToken = localStorage.getItem('temp_token');
    }

    
    // ENHANCED LOGIN METHOD FOR 2FA FLOW
    // handle login via mail + pass
    async login(email, password) {
        try {
            console.log('🔐 Attempting login...');
            // make post request to /auth/login with credentials
            const data = await this.request('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password }),
            });

            console.log('📨 Login response:', data);

            // enhanced flow: HANDLE 2FA REQUIRED RESPONSE
            if (data.requires_2fa) {
                console.log('🔄 2FA required - storing temporary state');
                this.pending2FA = true;
                this.tempToken = data.access_token; // Temporary token for 2FA verification
                this.userEmail = email;
                
                // Store 2FA state in localStorage
                localStorage.setItem('pending_2fa', 'true');
                localStorage.setItem('temp_token', data.access_token);
                localStorage.setItem('user_email', email);
                
                return {
                    requires2FA: true,
                    message: data.message
                };
            }

            // normal flow
            // store + return login response data
            this.setTokens(data.access_token, data.refresh_token);
            this.setUserEmail(data.user.email);

            //enhanced flow
            this.clear2FAState(); // CLEAR ANY PENDING 2FA STATE
            
            // normal flow
            ////return data;

            //instead for enhanced flow
            return {
                requires2FA: false,
                message: data.message,
                user: data.user
            };
        } catch (error) {
            console.error('❌ Login failed:', error);
            throw new Error('Login failed: ' + error.message);
        }
    }


    ////// The protected resource /auth/me fails after the fully successfull 2FA auth
    ////// because of the potential race condition in the previous implementation
    // Enhanced flow: COMPLETE 2FA LOGIN FLOW
    async complete2FALogin(code) {
        try {
            // VALIDATE 2FA STATE
            if (!this.pending2FA || !this.tempToken) {
                throw new Error('No pending 2FA login found');
            }

            console.log('🔄 Completing 2FA login...');

            // USE TEMP TOKEN FOR 2FA VERIFICATION
            // The temp token represents "credentials verified, 2FA pending"
            // We need to send it to verify the TOTP code
            
            // Store current token state
            const originalToken = this.accessToken; 
            // Temporarily use temp token for this request
            
            // !!!!!!!!! Beginning of race condition: Overwrites accessToken !!!!!!!!!
            this.accessToken = this.tempToken; 
            /*
            1. this.accessToken is the current authentication state used by all other methods

            2. When it is overwritten with a temporary 2FA pending token
            During the async request, other methods might try to use 
            this.accessToken thinking it's valid
            But it's now a temp token that only works for 2FA verification!
            */
            
            // VERIFY TOTP CODE WITH BACKEND
            // !!!!!!!!! Race condition: temp token call during async gap !!!!!!!!!
            const data = await this.request('/auth/verify-2fa', {
                method: 'POST',
                body: JSON.stringify({ code })
            });
            /*
            During this async gap:

            1. Other parts of your app might call this.request() for different endpoints
                They'll use the temp token instead of proper tokens
            2. Could get "Invalid token" errors for legitimate requests
            */

            // RESTORE TOKEN STATE AND SET NEW FULL TOKENS 
            // Restore previous token state

            // !!!!!!!!! Race condition: RESTORES OLD TOKEN (without 2FA) !!!!!!!!!
            ////$$ FIX: IMMEDIATELY SET NEW TOKENS BEFORE ANY STATE RESTORATION
            ////$$ This ensures the auth state is always moving forward, never backward

            // this.accessToken = originalToken; 
            /* ^^
            OLD token (from before 2FA verification) has is_2fa_verified: false
            For a brief moment, wrong (temp) token state is entered
            Before a call this.setTokens() with the new tokens
            */


            // RESTORE ORIGINAL TOKEN STATE AND SET NEW TOKENS
            // SET THE FULL AUTHENTICATED TOKENS (credentials + 2FA verified) 
            this.setTokens(data.access_token, data.refresh_token);
            /*    If any other code reads this.accessToken between these lines
            They might get the old unverified token instead of the new verified one
            This could explain why /auth/me fails initially*/

            this.setUserEmail(data.user.email);

            //$$ NOW safely restore any other state 
            // (though accessToken is already updated by setTokens)
            //$$ Redundant but explicit
            this.accessToken = data.access_token; 

            //CLEAN UP 2FA STATE
            // Clear temp token and pending state
            this.clear2FAState(); 
            
            console.log('✅ 2FA login completed successfully');
            return data;
            
        } catch (error) {
            //$$ HOTFIX: RESTORE STATE ON ERROR TO PREVENT CORRUPTED AUTH STATE
            this.accessToken = this.originalToken; 
            console.error('❌ 2FA login completion failed:', error);
            throw new Error('2FA verification failed: ' + error.message);
        }
    }

    // Enhanced flow: CLEAR 2FA STATE
    clear2FAState() {
        this.pending2FA = false;
        this.tempToken = null;
        localStorage.removeItem('pending_2fa');
        localStorage.removeItem('temp_token');
    }

    // Enhanced flow: CHECK IF 2FA LOGIN IS PENDING
    is2FAPending() {
        return this.pending2FA && this.tempToken;
    }

    // Enhanced flow: GET PENDING EMAIL FOR 2FA
    getPendingEmail() {
        return this.userEmail;
    }


    // existing, normal flow
    // generic api requests    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers, // merge additional headers
            },
            ...options, // include other options like method, body
        };

        // Add Authorization header if access token exists
        // and it's not a refresh token request 
        // (to avoid infinite loop)
        if (this.accessToken && !endpoint.includes('/refresh_token')) {
            config.headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        try { // to make api request
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            // rethrow error after log
            throw error;
        }
    }

    // modified to handle 2fa verification requirement
    async signup(userData) {
        try {
            // make post request using user data to /auth/signup
            const data = await this.request('/auth/signup', {
                method: 'POST',
                body: JSON.stringify(userData),
            });
            //// deprecated, data returned when no 2fa is needed on signup
            //return data;


            // !!!!!!!!! SIGNUP ALWAYS REQUIRES 2FA VERIFICATION !!!!!!!!!
            // !!!!!!!!! STORE TEMPORARY TOKEN FOR SIGNUP 2FA VERIFICATION !!!!!!!!!
            this.tempToken = data.temp_token;
            localStorage.setItem('temp_token', data.temp_token);
            localStorage.setItem('pending_2fa', 'true');

            // !!!!!!!!! RETURN SPECIAL RESPONSE INDICATING 2FA NEEDED FOR SIGNUP !!!!!!!!!
            return {
                requires2fa_verification: true,
                message: data.message,
                temp_token: data.temp_token,
                user_email: data.user_email
            };
            
        } catch (error) {
            throw new Error('Signup failed: ' + error.message);
        }
    }

    async refreshAccessToken() {
        if (!this.refreshToken) {
            throw new Error('No refresh token available');
        }

        try {        
            //log the changed states in console
            console.log('🔄 Attempting token refresh...');
            // get request to /auth/refresh_token
            const data = await this.request('/auth/refresh_token', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${this.refreshToken}`,
                },
            });
            //log the changed states in console
            console.log('✅ Token refresh response:', data);
            // update the access token in memory and local storage
            this.accessToken = data.access_token;
            localStorage.setItem('access_token', this.accessToken);
            //log the changed states in console
            console.log('🆕 New access token stored');
            // return data because of updated access token
            return data;
        } catch (error) {
            // FORCE LOGOUT the user if refresh fails
            // add error message for console
            console.error('❌ Token refresh failed:', error);
            this.logout();
            throw new Error('Token refresh failed: ' + error.message);
        }
    }

    //IMPORTANT! 
    // This is the automatic refresh access token functionality
    // The manual (button) one is defined in window.app.refreshToken()
    // both call auth.refreshAcessToken()
    // The modified version here first attempts to call
    // on window.app.handleAutoRefresh()
    ////note: potentially migrate above-mentioned helper method 
    //// to auth.js instead in the future
    async getCurrentUser() {
        try {
            console.log('👤 Fetching current user...');
            const data = await this.request('/auth/me');
            console.log('✅ Current user data:', data);
            return data;
        } catch (error) {
            console.log('❌ Get current user failed:', error.message);
            
            // If token is expired (403), try to refresh automatically
            if (error.message.includes('403') || error.message.includes('401')) {
                console.log('🔄 Token expired, attempting auto-refresh...');
                try {
                    // Call the auto-refresh handler if it exists
                    if (window.app && window.app.handleAutoRefresh) {
                        await window.app.handleAutoRefresh();
                    } else {
                        await this.refreshAccessToken();
                    }
                    
                    console.log('✅ Auto-refresh successful, retrying user data...');
                    return await this.getCurrentUser(); // Retry with new token
                } catch (refreshError) {
                    console.log('❌ Auto-refresh failed:', refreshError.message);
                    this.logout();
                    throw new Error('Session expired. Please login again.');
                }
            }
            throw error;
        }
    }

    // helper method: store tokens, both in memory and localStorage
    // store in memory by upgrading class properties 
    setTokens(accessToken, refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    }

    // helper method: store mail, both in memory and localStorage
    // store in memory by upgrading class properties 
    setUserEmail(email) {
        this.userEmail = email;
        localStorage.setItem('user_email', email);
    }

    // check if current user is authenticated
    isAuthenticated() {
        // return true if access token is not true or undefined
        return !!this.accessToken;
    }

    //enhanced logout
    // resets class properties and localStorage data
    logout() {
        this.accessToken = null;
        this.refreshToken = null;
        this.userEmail = null;
        this.clear2FAState(); // CLEAR 2FA STATE ON LOGOUT
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_email');
    }

    getUserEmail() {
        // from memory/ class property
        return this.userEmail;
    }
}