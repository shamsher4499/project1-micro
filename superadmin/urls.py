from .views import *
from django.urls import path
from . import views
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

urlpatterns = [
    path('dashboard/', views.homepage, name='homepage'),
        # ---------------------Auth urls-----------------
    path('login/', views.login, name='admin_login'),
    path('logout/', views.logout, name='admin_logout'),
    # path('borrower-report-list/', views.borrower_report_list, name='report_management'),
    path('generate-borrower-report/', views.borrowerGenerateReport, name='generate_borrower_report'),
    path('profile/', views.adminProfile, name='admin_profile'),
    path('forgetPasswordStep1/', views.forgetPasswordStep1, name='admin_forget_password_step1'),
    path('forgetPasswordStep2/<str:slug>/', views.forgetPasswordStep2, name='admin_forget_password_step2'),
    path('forgetPasswordStep3/<str:slug>/<str:user_slug>/', views.forgetPasswordStep3, name='admin_forget_password_step3'),

        #---------------Borrower----------------------
    path('usersListing/', views.borrowersListing, name='borrower_listing'),
    path('addUser/', views.borrowersAdd, name='add_borrower'),
    path('viewUser/<str:slug>/', views.borrowersView, name='view_borrower'),
    path('deleteUser/<str:slug>/', views.borrowersDelete, kwargs={'slug_user': None}, name='delete_borrower'),
    path('editUser/<str:slug>/', views.borrowersEdit, name='edit_borrower'),

        #---------------Store----------------------
    path('storeListing/', views.storeListing, name='store_listing'),
    path('viewStore/<str:slug>/', views.storeView, name='view_store'),
    path('editStore/<str:slug>/', views.storeEdit, name='edit_store'),
    path('addStore/', views.storeAdd, name='add_store'),
    path('deleteStore/<str:slug>/', views.storeDelete, kwargs={'slug_user': None}, name='delete_store'),

        #------------------Lender----------------------
    # path('lenderListing/', views.lendersListing, name='lender_listing'),
    # path('addLender/', views.lenderAdd, name='add_lender'),
    # path('viewLender/<str:slug>/', views.lenderView, name='view_lender'),
    # path('deleteLender/<str:slug>/', views.lenderDelete, name='delete_lender'),
    # path('editLender/<str:slug>/', views.lenderEdit, name='edit_lender'),

        #------------------Testimonial----------------------
    path('teamListing/', views.teamListing, name='testimonial_listing'),
    path('addTeam/', views.teamAdd, name='add_testimonial'),
    path('viewTeam/<str:slug>/', views.teamView, name='view_testimonial'),
    path('deleteTeam/<str:slug>/', views.teamDelete, name='delete_testimonial'),
    path('editTeam/<str:slug>/', views.teamEdit, name='edit_testimonial'),

        #------------------Social Account----------------------
    path('editSocial/', views.socialEdit, name='edit_social'),

    #------------------Loan Management----------------------
    path('editLoan/', views.loanLimitEdit, name='edit_loan'),
    path('Loans/', views.allLoanUser, name='all_loans'),
    path('viewLoan/<str:slug>/', views.LoanView, name='view_loans'),

        #------------------Edit Address----------------------
    path('addAddress/<str:slug>/', views.addressAdd, name='add_address'),
    path('editAddress/<str:slug>/', views.addressEdit, name='edit_address'),
    path('deleteAddress/<str:slug>/', views.addressDelete, name='delete_address'),

        #------------------Homepage Youtube Link----------------------
    path('editYouTube-id/', views.youtubeEdit, name='edit_youtube_id'),

        #------------------Homepage Youtube Link----------------------
    path('editHomepage-id/', views.homepageEdit, name='edit_homepage_id'),

        #------------------Inquiry----------------------
    path('inquiryListing/', views.inquiryListing, name='inquiry_listing'),
    path('inquiryReply/<str:slug>/', views.replyInquiry, name='inquiry_reply'),
    path('inquiryDelete/<str:slug>/', views.resolvedDelete, name='inquiry_delete'),
    path('resolvedListing/', views.inquiryResolvedListing, name='inquiry_resolved'),

        #------------------Email----------------------
    path('emailListing/', views.emailListing, name='email_listing'),
    path('addEmail/', views.emailAdd, name='add_email'),
    path('viewEmail/<str:slug>/', views.emailView, name='view_email'),
    path('deleteEmail/<str:slug>/', views.emailDelete, name='delete_email'),
    path('editEmail/<str:slug>/', views.emailEdit, name='edit_email'),
    
    # ---------------------Pending Users-----------------
    path('pendingUsers/', views.pendingUsersListing, name='pending_users'),
    path('pendingUsers-view/<str:slug>/', views.pendingUsersView, name='pending_users_view'),
    path('statusChanged-view/<str:slug>/', views.verifyPendingUsersView, name='pending_users_status_changed'),
    path('deletePendingUser/<str:slug>/', views.pendingUserDelete, name='pending_users_delete'),

    #---------------------------------------Blog----------------------------------------
    path('blogListing/', views.blogListing, name='blog_listing'),
    path('add-blog/', views.blogAdd, name='add_blog'),
    path('view-blog/<str:blog_slug>/<str:slug>/', views.blogView, name='view_blog'),
    path('delete-blog/<str:slug>/', views.blogDelete, name='delete_blog'),
    path('edit-blog/<str:blog_slug>/<str:slug>/', views.blogEdit, name='edit_blog'),

    #---------------------------------------About us----------------------------------------
    path('aboutListing/', views.aboutUsListing, name='about_listing'),
    # path('add-blog/', views.blogAdd, name='add_blog'),
    path('view-about-us/<str:slug>/', views.aboutUsListing, name='view_about_us'),
    # path('delete-blog/<str:slug>/', views.blogDelete, name='delete_blog'),
    path('edit-about-us/<str:slug>/', views.aboutUsEdit, name='edit_about_us'),

    #---------------------------------------FAQ----------------------------------------
    path('faqListing/', views.faqListing, name='faq_listing'),
    path('add-faq/', views.faqAdd, name='add_faq'),
    path('view-faq/<str:slug>/', views.faqView, name='view_faq'),
    path('delete-faq/<str:slug>/', views.faqDelete, name='delete_faq'),
    path('edit-faq/<str:slug>/', views.faqEdit, name='edit_faq'),

    #---------------------------------------Terms & Condition----------------------------------------
    path('edit-termsCondition/', views.termsEdit, name='edit_terms_condition'),

    #----------------------------------------Privacy Policy---------------------------------------
    path('edit-privacyPolicy/', views.privacyPolicyEdit, name='edit_privacy_policy'),

    #---------------------------------------wallet----------------------------------------
    path('walletListing/', views.walletListing, name='wallet_listing'),
    path('view-wallet/<str:slug>/', views.walletView, name='view_wallet'),
    path('edit-wallet/<str:slug>/', views.walletEdit, name='edit_wallet'),
    path('edit-walletAmount/', views.walletAmountLimitEdit, name='edit_wallet_amount'),

    #---------------------------------------Fake email----------------------------------------
    path('fakeEmailListing/', views.fakeEmailListing, name='fake_email_listing'),
    path('add-fakeEmail/', views.fakeEmailAdd, name='add_fake_email'),
    path('edit-fakeEmail/<str:slug>/', views.fakeEmailEdit, name='edit_fake_email'),
    path('delete-fakeEmail/<str:slug>/', views.fakeEmailDelete, name='delete_fake_email'),

    #---------------------------------------Plan Feature----------------------------------------
    path('featureListing/', views.planFeatureListing, name='feature_listing'),
    path('add-feature/', views.planFeatureAdd, name='add_feature'),
    path('edit-feature/<str:slug>/', views.planFeatureEdit, name='edit_feature'),
    path('activeUsers/', views.activeSubscriptionUser, name='active_users'),

    #---------------------------------------Subscription Plan----------------------------------------
    path('subscriptionListing/', views.subscriptionPlanListing, name='subscription_plan_listing'),
    path('add-subscriptionPlan/', views.subscriptionPlanAdd, name='add_subscription_plan'),
    path('edit-subscriptionPlan/<str:slug>/', views.subscriptionPlanEdit, name='edit_subscription_plan'),
    path('delete-subscriptionPlan/<str:slug>/', views.subscriptionPlanDelete, name='delete_subscription_plan'),
    path('view-subscriptionPlan/<str:slug>/', views.subscriptionPlanView, name='view_subscription_plan'),

        #---------------------------------------Store Tier ----------------------------------------
    path('store-tierListing/', views.tierListing, name='store_tier_listing'),
    path('add-storeTier/', views.tierAdd, name='add_store_tier'),
    path('edit-storeTier/<str:slug>/', views.tierEdit, name='edit_store_tier'),
    path('view-storeTier/<str:slug>/', views.tierView, name='view_store_tier'),

    #---------------------------------------Subscription Plan----------------------------------------
    path('store-subscriptionListing/', views.storeSubscriptionPlanListing, name='store_subscription_plan_listing'),
    path('add-store-subscriptionPlan/', views.storeSubscriptionPlanAdd, name='add_store_subscription_plan'),
    path('edit-store-subscriptionPlan/<str:slug>/', views.storeSubscriptionPlanEdit, name='edit_store_subscription_plan'),
    path('delete-store-subscriptionPlan/<str:slug>/', views.storeSubscriptionPlanDelete, name='delete_store_subscription_plan'),
    path('view-store-subscriptionPlan/<str:slug>/', views.storeSubscriptionPlanView, name='view_store_subscription_plan'),

    #---------------------------------------Report Management----------------------------------------
    path('generateUser-Report/', views.user_report_list, name='generate_user_report'),


    #---------------------------------------Dwolla Management----------------------------------------
    path('dwollaAccount/', views.adminAccountEdit, name='dwolla_account'),
    path('adminEarning/', views.adminEarning, name='admin_earning'),
    path('lenderEarning/', views.lenderEarning, name='lender_earning'),

    #---------------------------------------Webhooks----------------------------------------
    path('generate-pdf/', views.TestPdf, name='test_pdf'),

    path('testing-webhooks/', views.TestSubscriptionCompletedwebhook, name='webhook_subscription'),
    

    #-------------------------------------prometheus--------------------------------
    path('metrics', lambda r: HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST), name='prometheus-metrics'),
]
