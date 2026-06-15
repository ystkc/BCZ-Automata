namespace py thriftAPI

# C:冷启动
# S:热启动
# 无标签:非必需
# 通用参数
exception LogicException {
    1: string from_service
    2: string from_method
    3: i32 code
    4: string message
}

exception SystemException {
    1: string from_service
    2: string from_method
    3: i32 code
    4: string message
}

# 用户认证和登录授权服务
## 电话号码登陆
struct PhoneFreeVerifyRequest {
    1: string clientToken,
    2: string opToken,
    3: string operatorName
}

struct PhoneVerifyCodeRequest {
    1: string phone,
    2: string verify_code
}

struct PhoneLoginRequest {
    1: PhoneVerifyCodeRequest verify_code_request,
    2: PhoneFreeVerifyRequest free_verify_request,
    3: string device
}

struct RoleInfo {
    1: bool role_up,
    2: i32 grade
}

struct UserLoginResult {
    1: string access_token,
    2: bool is_new_user,
    3: string email,
    4: string public_key,
    5: string last_device,
    6: i64 unique_id,
    7: string phone,
    8: i32 force_bind_phone,
    9: i32 role_new,
    10: RoleInfo role
}

struct login_with_phone_args {
    1: PhoneLoginRequest request
}
struct send_sms_verify_code_args {
    1: string phone,
    2: i32 verify_type
}

## get_bind_info
struct UserBindInfo{
    1: string provider,
    2: string openid,
    3: string unionid,
    4: string nickname
}
struct get_bind_info_result{
    1: list<UserBindInfo> success,
    2: SystemException boom,
    3: LogicException bomb
}

## check_access_token
struct check_access_token_args{
    1: string device
}
struct AccessTokenCheckResult{
    1: string access_token,
    2: string last_device,
    3: bool is_new_user
}
struct check_access_token_result{
    1: AccessTokenCheckResult success,
    2: SystemException boom,
    3: LogicException bomb
}
struct update_role_extra_args{
    1: i32 grade,
    2: i32 role_up
}
struct update_role_extra_result{
    1: string success,
    2: SystemException boom,
    3: LogicException bomb
}
service UnifiedUserService {
    void send_sms_verify_code(1: send_sms_verify_code_args args_)
    UserLoginResult login_with_phone(1: login_with_phone_args args_) throws (1: LogicException bomb, 2: SystemException boom) 
    # C
    list<UserBindInfo> get_bind_info() throws (1: LogicException bomb, 2: SystemException boom) 
    # C, S
    AccessTokenCheckResult check_access_token(1: string device) throws (1: LogicException bomb, 2: SystemException boom) 
    # Other(Change Grade)
    string update_role_extra(1: i32 grade, 2: i32 role_up) throws (1: LogicException bomb, 2: SystemException boom) 
}










# 书本和词库服务
## 获取用户信息
struct EducationInfo {
    1: i32 school_id,
    2: string school_name,
    3: i64 school_year,
    4: i32 major_id,
    5: string school_major,
    6: i32 school_bg,
    7: bool is_university
}

struct UserBasicInfoV2 {
    1: i32 current_word_level_id,
    2: string current_word_level_name,
    3: i32 gender_id,
    4: string nickname,
    5: string avatar,
    6: i64 birthday,
    7: string position,
    8: EducationInfo user_education_info,
    9: string current_book_desc,
    10: string current_book_desc_img,
    11: RoleInfo role,
    12: string ip_desc,

}

struct WikiComponent{
    1: i32 id,
    2: i32 priority,
    3: i32 enable
}

struct UserLimitInfoV2 {
    1: i32 show_sentence_trans,
    2: i32 has_word_friends,
    3: i32 spell_mode,
    4: i32 listening_mode,
    5: i32 chn_mode,
    6: i64 update_at_of_book_info,
    7: i64 update_at_of_notify_info,
    8: i64 collect_words_updated_at,
    9: i64 word_note_updated_at,
    10: i32 cur_book_has_primary_school_mode,
    11: i32 word_note_enable,
    12: list<WikiComponent> wiki_component_cfg,
    13: i32 new_wiki,
    14: i32 chn_style,
    15: i32 show_device,
    16: i32 current_mode,
    17: string x_mode_setting,
    18: i32 show_topic_correction,
    19: i64 server_timestamp
}

struct UserLearnInfoV2 {
    1: i64 last_sync_done_score_time,
    2: i32 daily_plan_count,
    3: i32 review_plan_count
}

struct UserBasicInfoPlusV2 {
    1: UserBasicInfoV2 user_info,
    2: UserLimitInfoV2 limit_info,
    3: UserLearnInfoV2 learn_info
}
## 上传完成学习信息
struct UserDoneWordRecord {
    1: i32 word_topic_id,
    2: i32 current_score,
    3: i32 span_days,
    4: i32 used_time,
    5: i32 done_times,
    6: i32 wrong_times,
    7: i32 is_first_do_at_today,
    8: i32 tag_id,
    9: i32 spell_score,
    10: i32 listening_score,
    11: i32 chn_score,
    12: i32 review_round
}

struct update_done_data_args {
    1: i64 last_sync_at,
    2: list<UserDoneWordRecord> arr_done_records,
    3: i32 current_word_level_id,
    4: bool is_today_completed
}

## 更换词书
struct ExamPreparation {
    1: i32 userType,
    2: string questionnaireUrl,
    3: string newStudyUrl,
    4: string reviewUrl,
    5: string generalReviewUrl
}
struct select_book_args {
    1: i32 book_id,
    2: i32 daily_plan_count,
    3: i32 review_plan_count,
    4: i32 mode
}
struct UserSelectedBookInfo {
    1: i32 book_id,
    2: i64 selected_end_time,
    3: i32 learned_words_count,
    4: i64 last_touch_at,
    5: i64 roadmap_version,
    6: i32 word_fm_updated_at,
    7: i32 group_id,
    8: i32 daily_plan_count,
    9: i64 poster_updated_at,
    10: i32 need_merge_count,
    11: i32 review_plan_count,
    12: ExamPreparation examPreparation,
    13: string mode_switch_url
}


## 获取书本详情
struct BookLevelInfo {
    1: i32 role_id,
    2: list<string> cate_ids,
    3: list<string> next_cates,
    4: string cate_name
}

struct UserBookBasicInfo {
    1: i32 id,
    2: string name,
    3: i32 total_words_count,
    4: bool is_word_course,
    5: i32 group_count,
    6: i32 book_flag,
    7: string img,
    8: string desc
}

struct UserBookCategory {
    1: string category_name,
    2: list<UserSubCategory> sub_categories,
    3: string tag_name,
    4: string cate_id
}

struct UserSubCategory {
    1: string sub_name,
    2: list<i32> book_ids
}

struct UserBookListInfo {
    1: list<UserBookBasicInfo> books_info,
    2: list<UserBookCategory> categories_info,
    3: list<BookLevelInfo> levels_info,
    4: list<BookLevelInfo> all_tops
}
struct get_all_books_basic_info_v3_args{
    1: UserBookListInfo book_list_info
}
## win_streak_status
struct win_streak_status_args{
    1: i32 client_date
}
struct WinStreakStatus{
    1: i32 enable,
    2: i32 win_streak_days,
    3: i32 latest_win_streak_date,
    4: i32 enableExperienceRanking,
    5: i32 taskStatus
}
struct win_streak_status_result{
    1: WinStreakStatus success,
    2: SystemException boom,
    3: LogicException bomb
}
## submit_win_streak_records
struct submit_win_streak_records_args{
    1: i32 client_date,
    2: list<i32> win_streak_dates
}
struct submit_win_streak_records_result{
    1: SystemException boom,
    2: LogicException bomb
}
## user_limit_info_v2
struct user_limit_info_v2_result{
    1: UserLimitInfoV2 success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_user_study_config
struct UserStudyConfig{
    1: i32 fast_mode,
    2: i32 chn_mode,
    3: i32 listening_mode,
    4: i32 spell_mode,
    5: string extra_config,
    6: bool is_pi_mode
}
struct get_user_study_config_result{
    1: UserStudyConfig success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_user_study_mode
struct UserStudyMode{
    1: i32 review_mode
}
struct get_user_study_mode_result{
    1: UserStudyMode success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_books_replace_info
struct BookReplaceInfo{
    1: i32 old_book_id,
    2: i32 new_book_id,
    3: string main_page_popup_title,
    4: string main_page_popup_content,
    5: string main_page_popup_ok_text,
    6: string main_page_popup_cancel_text,
    7: bool force_update
}
struct get_books_replace_info_result{
    1: list<BookReplaceInfo> success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_main_page_js
struct MainPageJS{
    1: i64 version,
    2: string jsUrl
}
struct get_main_page_js_result{
    1: MainPageJS success,
    2: SystemException boom,
    3: LogicException bomb
}
## user_daka_v2  
struct UserDakaDate{
    1: i32 year,
    2: i32 month,
    3: i32 day,
    4: i64 timestamp
}
struct UserDakaTopic{
    1: i32 topic_id,
    2: i32 wrong_times,
    3: i32 done_times
}
    
struct UserDakaRequest{
    1: i32 book_id,
    2: i32 count,
    3: list<UserDakaDate> daka_dates,
    4: string timezone,
    5: UserDakaDate client_date,
    6: list<UserDakaTopic> poster_topic_ids
}
struct user_daka_v2_args{
    1: UserDakaRequest request
}
struct UserDakaSpecialDay{
    1: UserDakaDate date,
    2: string img_url
}
struct UserDakaShareInfo{
    1: string weibo_share_txt,
    2: string weibo_share_img_url,
    3: string weixin_share_title,
    4: string weixin_share_url,
    5: list<string> weixin_share_pic_urls,
    6: string qzone_share_url,
    7: i32 total_daka_days,
    8: list<UserDakaDate> daka_dates,
    9: list<UserDakaSpecialDay> special_days,
    10: string xhs_share_title,
    11: string xhs_share_content
}
struct user_daka_v2_result{
    1: UserDakaShareInfo success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_train_page_resource
struct TrainPageBannerItem{
    1: string aid,
    2: string img,
    3: i32 action,
    4: string link
}
enum ModuleResourceType{
    WORD_LISTENING = 1,
    WORD_CHECK = 2,
    ENGLISH_RECOGNIZED = 3,
    CHINESE_RECOGNIZED = 4,
    LISTENING_RECOGNIZED = 5,
    FILL_BLANK_SPELLING = 6,
    COMBINE_SPELLING = 7,
    ALL_SPELLING = 8,
    WORD_READING = 9,
    WORD_VIDEO = 10,
    WORD_RADIO = 11,
    WORD_TRAINING = 12
}
struct TrainPageResource{
    1: list<ModuleResourceType> items,
    2: string module_name
}
struct ResourceItem{
    1: string aid,
    2: string title,
    3: string img,
    4: i32 action,
    6: string link,
    7: i32 type
}
struct TrainPageResources{
    1: bool enable,
    2: list<ResourceItem> outerResource,
    3: list<TrainPageResource> resources,
    4: TrainPageBannerItem banner
}
struct get_train_page_resource_result{
    1: TrainPageResources success,
    2: SystemException boom,
    3: LogicException bomb
}
## submit_experience_record
struct StudyExperienceRecord{
    1: string questionType,
    2: i32 behavior,
    3: i32 cnt
}
struct submit_experience_record_args{
    1: list<StudyExperienceRecord> records,
}
struct submit_experience_record_result{
    1: SystemException boom,
    2: LogicException bomb
}
## get_daka_background_datas
struct get_daka_background_datas_args{
    1: list<i32> topic_ids
}
struct DakaBackgroundCategoryInfo{
    1: string name,
    2: list<string> images,
    3: list<string> colors,
    4: list<i64> image_ids,
    5: string sentence,
    6: string sen_mean,
    7: string sen_source,
    8: i32 win_days,
    9: i32 win_type
}
struct DakaBackgroundData{
    1: list<DakaBackgroundCategoryInfo> category_info,
    2: string logo,
    3: string title,
    4: string qr_image
}
struct get_daka_background_datas_result{
    1: DakaBackgroundData success,
    2: SystemException boom,
    3: LogicException bomb
}
## share_bonus
struct share_bonus_args{
    1: i64 client_timestamp_ms
}
struct DakaShareBonusResult{
    1: i32 coinCount,
    2: i32 status,
    3: string message,
    4: string shareSuccess,
    5: string extraTip,
    6: string action,
    7: string actionUrl
}
struct share_bonus_result{
    1: DakaShareBonusResult success,
    2: SystemException boom,
    3: LogicException bomb
}
## credit_task_center
struct Task{
    1: i32 task_id,
    2: i32 task_type,
    3: string task_title,
    4: string task_sub_title,
    5: string award,
    6: i32 status,
    7: string button_desc,
    8: i32 button_action_type,
    9: string button_redirect_url
}
struct CreditCenter{
    1: i32 show_credit_center,
    2: i32 credit,
    3: i32 daily_inc_credit,
    4: list<string> credit_item_img,
    5: i32 new_flag,
    6: string credit_mall_url,
    7: list<Task> task
}
struct credit_task_center_result{
    1: CreditCenter success,
    2: SystemException boom,
    3: LogicException bomb
}
## upload_task_action
struct upload_task_action_args{
    1: list<TaskUploadReq> req
}
struct TaskUploadReq{
    1: string action,
    2: i32 cnt
}
## bcz_login
struct bcz_login_args{
    1: BczLoginRequest param,
}
struct BczLoginRequest{
    1: string account,
    2: string password
    3: string device,
    4: string code,
}
struct bcz_login_result{
    1: UserLoginResult success,
    2: SystemException boom,
    3: LogicException bomb
}

service UserStudyApiService {
    UserSelectedBookInfo select_book(1: select_book_args args_)
    i32 update_done_data(1: i64 last_sync_at, 2: list<UserDoneWordRecord> arr_done_records, 3: i32 current_word_level_id, 4: bool is_today_completed) throws (1: LogicException bomb, 2: SystemException boom)
    UserBookListInfo get_all_books_basic_info_v3() throws (1: LogicException bomb, 2: SystemException boom)
    void submit_experience_record(1: list<StudyExperienceRecord> records) throws (1: LogicException bomb, 2: SystemException boom)
    DakaBackgroundData get_daka_background_datas(1: list<i32> topic_ids) throws (1: LogicException bomb, 2: SystemException boom)
    DakaShareBonusResult share_bonus(1: i64 client_timestamp_ms) throws (1: LogicException bomb, 2: SystemException boom)
    CreditCenter credit_task_center() throws (1: LogicException bomb, 2: SystemException boom)
    void upload_task_action(1: list<TaskUploadReq> req) throws (1: LogicException bomb, 2: SystemException boom)
    # C
    UserBasicInfoPlusV2 user_basic_info_v2() throws (1: LogicException bomb, 2: SystemException boom)
    UserStudyConfig get_user_study_config() throws (1: LogicException bomb, 2: SystemException boom)
    UserStudyMode get_user_study_mode() throws (1: LogicException bomb, 2: SystemException boom)
    # C, S
    UserLimitInfoV2 user_limit_info_v2() throws (1: LogicException bomb, 2: SystemException boom)
    WinStreakStatus win_streak_status(1: i32 client_date) throws (1: LogicException bomb, 2: SystemException boom)
    # None
    void submit_win_streak_records(1: i32 client_date, 2: list<i32> win_streak_dates) throws (1: LogicException bomb, 2: SystemException boom)
    UserLoginResult bcz_login(1: bcz_login_args args_) throws (1: LogicException bomb, 2: SystemException boom)
    # C
    list<BookReplaceInfo> get_books_replace_info() throws (1: LogicException bomb, 2: SystemException boom)
    MainPageJS get_main_page_js() throws (1: LogicException bomb, 2: SystemException boom)
    UserDakaShareInfo user_daka_v2(1: user_daka_v2_args args_) throws (1: LogicException bomb, 2: SystemException boom)
    TrainPageResources get_train_page_resource() throws (1: LogicException bomb, 2: SystemException boom)
}







# bcz_system_service
## check_infos
struct BczSystemInfos {
    1: list<string> res_dns,
    2: list<string> data_dns,
    3: map<string, list<string>> other_dns,
    4: map<string, list<string>> tls_dns
}
struct check_infos {
    1: BczSystemInfos success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_switches
struct BczAppSwitch {
    1: bool allow_try_user,
    2: bool allow_fast_login
}
struct get_switches {
    1: BczAppSwitch success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_app_beta_update_info
struct AppBetaUpdateRequest{
    1: string device_id,
    2: string device_manufacturer,
    3: string device_model,
    4: string os_name,
    5: string os_sdk,
    6: string short_version,
    7: i32 long_version,
    8: string app_channel,
    9: string app_name
}
struct get_app_beta_update_info_args{
    1: AppBetaUpdateRequest request
}
struct AppBetaUpdateResult{
    1: i32 type,
    2: string version_description,
    3: string version_url,
    4: string version_apk_md5,
    5: string new_version
}
struct get_app_beta_update_info_result{
    1: AppBetaUpdateResult success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_privacy_agreement_version
struct PrivacyAgreementInfo{
    1: string content,
    2: i32 privacy_version,
    3: map<string, string> privacy_urls
}
struct get_privacy_agreement_version_result{
    1: PrivacyAgreementInfo success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_domain_whitelist
struct get_domain_whitelist_result{
    1: list<string> success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_static_config
struct StaticConfig{
    1: string key,
    2: i32 bit_flag,
    3: string config_json
}
struct get_static_config_result{
    1: list<StaticConfig> success,
    2: SystemException boom,
    3: LogicException bomb
}
service bcz_system_service {
    # Cx3, S
    BczSystemInfos check_infos() throws (1: LogicException bomb, 2: SystemException boom)
    # C
    BczAppSwitch get_switches() throws (1: LogicException bomb, 2: SystemException boom)
    list<StaticConfig> get_static_config() throws (1: LogicException bomb, 2: SystemException boom)
    list<string> get_domain_whitelist() throws (1: LogicException bomb, 2: SystemException boom)
    PrivacyAgreementInfo get_privacy_agreement_version() throws (1: LogicException bomb, 2: SystemException boom)
    AppBetaUpdateResult get_app_beta_update_info(1: get_app_beta_update_info_args args_) throws (1: LogicException bomb, 2: SystemException boom)
}




# advertise_service 
## get_startup_ad
struct StartupAdRequest{
    1: i32 screen_length,
    2: i32 screen_width,
    3: string android_id,
    4: string oaid
}
struct get_startup_ad_args{
    1: StartupAdRequest request
}


struct AdLink{
    1: i32 jump_type,
    2: string link,
    3: string mini_program_id,
    4: string mini_program_path
}
struct StartupAd{
    1: i32 ad_id,
    2: string img,
    3: i64 start_time,
    4: i64 end_time,
    5: i32 show_times,
    6: i32 show_seconds,
    7: AdLink link,
    8: AdLink backup_link,
    9: string ext_ad_id,
    10: i32 ad_type,
    11: i32 full
}
struct get_startup_ad_result{
    1: LogicException bomb,
    2: SystemException boom,
    3: list<StartupAd> success
}
## get_live_streaming_info
struct LiveStreamingInfo{
    1: i64 current_timestamp,
    2: i64 start_timestamp,
    3: i64 end_timestamp
}
struct get_live_streaming_info_result{
    1: LiveStreamingInfo success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_practice_popup_adv   
struct PracticePopupAdv{
    1: string id,
    2: string img,
    3: string link
}
struct get_practice_popup_adv_result{
    1: PracticePopupAdv success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_explore_popup_adv
struct ExplorePopupAdv{
    1: string id,
    2: string img,
    3: string link
}
struct get_explore_popup_adv_result{
    1: ExplorePopupAdv success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_mall_tab_icon_info
struct MallIconItem{
    1: string aid,
    2: string icon_normal,
    3: string icon_press,
    4: i64 start_time,
    5: i64 end_time,
    6: string mall_name
}
struct MallTabInfo{
    1: i32 recommendType,
    2: list<MallIconItem> taobao,
    3: list<MallIconItem> mall
}
struct get_mall_tab_icon_info_result{
    1: MallTabInfo success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_loading_ad_items
enum AdvertiseRedirectType{
    REDIRECT_NOTHING = 0,
    REDIRECT_TAOBAO = 1,
    REDIRECT_BROWSER = 2,
    REDIRECT_SYS_NOTIFY = 3,
    REDIRECT_LOCAL_STORE = 4,
    REDIRECT_PI = 5,
    REDIRECT_ONLY_NATIVE_MALL = 6
}
struct AdvertiseRedirectInfo{
    1: AdvertiseRedirectType redirect_type,
    2: string redirect_url,
    3: string taobao_item_id,
    4: i32 sys_notify_id,
    5: string mall_url
}
struct AdvertiseLoadingItem{
    1: i32 ad_id,
    2: string ad_name,
    3: string image_url,
    4: i32 show_time
    5: double btn_x,
    6: double btn_y,
    7: double btn_w,
    8: double btn_h,
    9: AdvertiseRedirectInfo redirect_info
}
struct get_loading_ad_items_result{
    1: list<AdvertiseLoadingItem> success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_loading_ad_info
enum AdvertiseLoadingModule{
    MODULE_FM = 1,
    MODULE_MAIN = 2,
    MODULE_PK = 3
}
struct AdvertiseLoadingInfo{
    1: list<i32> ad_ids,
    2: AdvertiseLoadingModule module_name
}
struct get_loading_ad_info_result{
    1: list<AdvertiseLoadingInfo> success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_main_view_bottom_advs_v2
struct MainViewBottomAdv{
    1: string id,
    2: string img_url,
    3: string link
    4: string aid,
}
struct BottomAdvInfos{
    1: list<MainViewBottomAdv> carousel_banner,
    2: list<MainViewBottomAdv> horizontal_banner,
    3: list<MainViewBottomAdv> grid_ad
}
struct get_main_view_bottom_advs_v2_result{
    1: BottomAdvInfos success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_practice_banner_adv
struct PracticeBannerAdv{
    1: string id,
    2: string img,
    3: string link
}
struct get_practice_banner_adv_result{
    1: PracticeBannerAdv success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_main_view_top_banner_advs
struct MainViewTopBannerAdv{
    1: string id,
    2: bool isDark,
    3: string img_url,
    4: string img_gradient_color,
    5: i32 img_type,
    6: i64 start_time,
    7: i64 end_time,
    8: string link,
    9: string aid
}
struct get_main_view_top_banner_advs_result{
    1: list<MainViewTopBannerAdv> success,
    2: SystemException boom,
    3: LogicException bomb
}
service advertise_service{
    # C, S
    list<StartupAd> get_startup_ad(1: get_startup_ad_args args_) throws (1: LogicException bomb, 2: SystemException boom)
    # C
    MallTabInfo get_mall_tab_icon_info() throws (1: LogicException bomb, 2: SystemException boom)
    # C, S
    PracticePopupAdv get_practice_popup_adv() throws (1: LogicException bomb, 2: SystemException boom)
    ExplorePopupAdv get_explore_popup_adv() throws (1: LogicException bomb, 2: SystemException boom)
    list<AdvertiseLoadingItem> get_loading_ad_items() throws (1: LogicException bomb, 2: SystemException boom)
    list<AdvertiseLoadingInfo> get_loading_ad_info() throws (1: LogicException bomb, 2: SystemException boom)
    LiveStreamingInfo get_live_streaming_info() throws (1: LogicException bomb, 2: SystemException boom)
    BottomAdvInfos get_main_view_bottom_advs_v2() throws (1: LogicException bomb, 2: SystemException boom)
    list<MainViewTopBannerAdv> get_main_view_top_banner_advs() throws (1: LogicException bomb, 2: SystemException boom)
    # C
    PracticeBannerAdv get_practice_banner_adv() throws (1: LogicException bomb, 2: SystemException boom)
}













# assistant_service
## check_feedback_msg

struct check_feedback_msg_args{
    1: string device_id
}
struct check_feedback_msg_result{    
    1: i32 success,
    2: SystemException boom,
    3: LogicException bomb
}
struct test{    
    1: i32 success
}
## get_activity_updated_time
struct get_activity_updated_time_result{
    1: i32 success,
    2: SystemException boom,
    3: LogicException bomb
}
## get_beta_user_types_v2
struct UserBetaInfo{
    1: list<i32> beta_types,
    2: list<i32> high_level_book_ids,
    3: list<i32> daka_poster_book_ids
}
struct get_beta_user_types_v2_result{
    1: UserBetaInfo success,
    2: SystemException boom,
    3: LogicException bomb
}


service assistant_service{
    # C, S
    i32 check_feedback_msg(1: string device_id) throws (1: LogicException bomb, 2: SystemException boom)
    i32 get_activity_updated_time() throws (1: LogicException bomb, 2: SystemException boom)
    UserBetaInfo get_beta_user_types_v2() throws (1: LogicException bomb, 2: SystemException boom)
}








# bcz_report_service

struct report_event_args{
    1: list<string> jsons
}
struct report_event_result{
    1: SystemException boom,
    2: LogicException bomb
}
service bcz_report_service{
    void report_event(1: list<string> jsons) throws (1: LogicException bomb, 2: SystemException boom)
}








# notify_service
## get_remind_info
struct UserRemindInfo{
    1: bool enable,
    2: i32 hour,
    3: i32 minute,
    4: bool wx_enable,
    5: i32 task_enable,
    6: i32 social_enable,
    7: i32 sentence_enable
}
struct get_remind_info_result{
    1: UserRemindInfo success,
    2: SystemException boom,
    3: LogicException bomb  
}

## get_latest_notify
struct Feedback{
    1: list<string> selection,
    2: string toast
}
struct Notify{
    1: i32 time,
    2: string title,
    3: string content,
    4: string url
    5: string img_url,
    6: string banner_img_url,
    7: string aid,
}
struct NotifyResult{
    1: i32 popup,
    2: i32 reddot,
    3: string service_url
    4: i32 count,
    5: Notify emergency,
    6: Notify notify,
    7: Notify advNotify,
    8: Feedback advFeedback,
}
struct get_latest_notify_result{
    1: NotifyResult success,
    2: SystemException boom,
    3: LogicException bomb
}


service notify_service{
    # C, S
    UserRemindInfo get_remind_info() throws (1: LogicException bomb, 2: SystemException boom)
    NotifyResult get_latest_notify() throws (1: LogicException bomb, 2: SystemException boom)
}




# resource_api_service
## get_book_resource_update_info
struct get_book_resource_update_info_args{
    1: i32 word_level_id
}
struct BookResourceUpdateInfo{
    1: i32 book_id,
    2: i64 zpk_updated_at,
    3: i64 word_fm_updated_at,
    4: i64 poster_updated_at,
    5: i64 roadmap_version,
    6: i64 tv_topic_updated_at
}
struct get_book_resource_update_info_result{
    1: BookResourceUpdateInfo success,
    2: SystemException boom,
    3: LogicException bomb
}
service resource_api_service{    
    # C
    BookResourceUpdateInfo get_book_resource_update_info(1: i32 word_level_id) throws (1: LogicException bomb, 2: SystemException boom)
}


# social_service

## exceptions

exception BESystemException{
    1: string from_service,
    2: string from_method,
    3: i32 code,
    4: string message
}
exception BELogicException{
    1: string from_service,
    2: string from_method,
    3: i32 code,
    4: string message
}


## send_share_success
enum BBShareModule{
    SHARE_MODULE_DAKA = 0,
}
enum BBShareChannel{
    SHARE_CHANNEL_WEIXIN_CIRCLE = 0,
    SHARE_CHANNEL_WEIXIN_FRIEND = 1,
    SHARE_CHANNEL_SINA = 2,
    SHARE_CHANNEL_QQ_CIRCLE = 3,
    SHARE_CHANNEL_QQ_FRIEND = 4
}
struct send_share_success_args{
    1: BBShareModule module_name,
    2: i64 timestamp,
    3: BBShareChannel channel
}
struct send_share_success_result{
    1: bool success,
    2: BESystemException sysException,
    3: BELogicException logicException
}
service social_service{
    # None
    bool send_share_success(1: BBShareModule module_name, 2: i64 timestamp, 3: BBShareChannel channel) throws (1: BELogicException logicException, 2: BESystemException sysException)
}