namespace py thriftAPI

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

# 上传完成学习信息
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



# 获取用户信息
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



# 更换词书
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


# 获取书本详情
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



# 电话号码登陆
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

service UnifiedUserService {
    void send_sms_verify_code(1: send_sms_verify_code_args args_)
    UserLoginResult login_with_phone(1: login_with_phone_args args_) throws (1: LogicException bomb, 2: SystemException boom) 
}

service UserStudyApiService {
    UserSelectedBookInfo select_book(1: select_book_args args_)
    i32 update_done_data(1: update_done_data_args args_)
    UserBookListInfo get_all_books_basic_info_v3() throws (1: LogicException bomb, 2: SystemException boom)
    UserBasicInfoPlusV2 user_basic_info_v2()
}



# check_infos
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
service check_infos_service {
    BczSystemInfos check_infos()
}

# get_switches
struct BczAppSwitch {
    1: bool allow_try_user,
    2: bool allow_fast_login
}
struct get_switches {
    1: BczAppSwitch success,
    2: SystemException boom,
    3: LogicException bomb
}
service get_switches_service {
    BczAppSwitch get_switches()
}

# get_startup_ad
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
service get_startup_ad_service{
    list<StartupAd> get_startup_ad(1: get_startup_ad_args args_) throws (1: LogicException bomb, 2: SystemException boom)
}