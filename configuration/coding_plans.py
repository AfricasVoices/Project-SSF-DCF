from core_data_modules.cleaners import somali, swahili, Codes
from core_data_modules.traced_data.util.fold_traced_data import FoldStrategies

from configuration import code_imputation_functions
from configuration.code_schemes import CodeSchemes
from src.lib.configuration_objects import CodingConfiguration, CodingModes, CodingPlan


def clean_age_with_range_filter(text):
    """
    Cleans age from the given `text`, setting to NC if the cleaned age is not in the range 10 <= age < 100.
    """
    age = swahili.DemographicCleaner.clean_age(text)
    if type(age) == int and 10 <= age < 100:
        return str(age)
        # TODO: Once the cleaners are updated to not return Codes.NOT_CODED, this should be updated to still return
        #       NC in the case where age is an int but is out of range
    else:
        return Codes.NOT_CODED


def clean_district_if_no_mogadishu_sub_district(text):
    mogadishu_sub_district = somali.DemographicCleaner.clean_mogadishu_sub_district(text)
    if mogadishu_sub_district == Codes.NOT_CODED:
        return somali.DemographicCleaner.clean_somalia_district(text)
    else:
        return Codes.NOT_CODED


def make_rqa_coding_plan(episode_name, code_scheme, ws_match_value, coda_filename):
    return CodingPlan(dataset_name=episode_name.replace("rqa_", ""),
                      raw_field=f"{episode_name}_raw",
                      time_field="sent_on",
                      run_id_field=f"{episode_name}_run_id",
                      coda_filename=f"{coda_filename}.json",
                      icr_filename=f"{coda_filename.lower()}.csv",
                      coding_configurations=[
                          CodingConfiguration(
                                coding_mode=CodingModes.MULTIPLE,
                                code_scheme=code_scheme,
                                coded_field=f"{episode_name}_coded",
                                analysis_file_key=f"{episode_name}",
                                fold_strategy=lambda x, y: FoldStrategies.list_of_labels(code_scheme, x, y)
                          )],
                      ws_code=CodeSchemes.WS_CORRECT_DATASET_SCHEME.get_code_with_match_value(ws_match_value),
                      raw_field_fold_strategy=FoldStrategies.concatenate)


def get_rqa_coding_plans(pipeline_name):
    if pipeline_name == "SSF-DCF":
        return [make_standard_rqa_coding_plan(episode_name="rqa_dcf_s01e01", code_scheme=CodeSchemes.S01E01,
                                              ws_match_value="ssf dcf s01e01", coda_filename="SSF_DCF_s01e01"),

                make_standard_rqa_coding_plan(episode_name="rqa_dcf_s01e02", code_scheme=CodeSchemes.S01E02,
                                              ws_match_value="ssf dcf s01e02", coda_filename="SSF_DCF_s01e02"),

                make_standard_rqa_coding_plan(episode_name="rqa_dcf_s01e03", code_scheme=CodeSchemes.S01E03,
                                              ws_match_value="ssf dcf s01e03", coda_filename="SSF_DCF_s01e03"),

                make_standard_rqa_coding_plan(episode_name="rqa_dcf_s01e04", code_scheme=CodeSchemes.S01E04,
                                              ws_match_value="ssf dcf s01e04", coda_filename="SSF_DCF_s01e04")]
    else:
        assert pipeline_name == "SSF-SLD"
        return [make_standard_rqa_coding_plan(episode_name="rqa_sld_s01e01", code_scheme=CodeSchemes.SLD_S01E01,
                                              ws_match_value="ssf sld s01e01", coda_filename="SSF_SLD_s01e01")]


def get_demog_coding_plans(pipeline_name):
    return [
        CodingPlan(raw_field="gender_raw",
                   time_field="gender_time",
                   coda_filename="IMAQAL_gender.json",
                   coding_configurations=[
                       CodingConfiguration(
                           coding_mode=CodingModes.SINGLE,
                           code_scheme=CodeSchemes.GENDER,
                           cleaner=somali.DemographicCleaner.clean_gender,
                           coded_field="gender_coded",
                           analysis_file_key="gender",
                           fold_strategy=FoldStrategies.assert_label_ids_equal,
                       )
                   ],
                   ws_code=CodeSchemes.WS_CORRECT_DATASET_SCHEME.get_code_with_match_value("gender"),
                   raw_field_fold_strategy=FoldStrategies.assert_equal),

        CodingPlan(raw_field="age_raw",
                   time_field="age_time",
                   coda_filename="IMAQAL_age.json",
                   coding_configurations=[
                       CodingConfiguration(
                           coding_mode=CodingModes.SINGLE,
                           code_scheme=CodeSchemes.AGE,
                           cleaner=lambda text: clean_age_with_range_filter(text),
                           coded_field="age_coded",
                           analysis_file_key="age",
                           fold_strategy=FoldStrategies.assert_label_ids_equal,
                           include_in_theme_distribution=False
                       ),
                       CodingConfiguration(
                           coding_mode=CodingModes.SINGLE,
                           code_scheme=CodeSchemes.AGE_CATEGORY,
                           coded_field="age_category_coded",
                           analysis_file_key="age_category",
                           fold_strategy=FoldStrategies.assert_label_ids_equal,
                       )
                   ],
                   code_imputation_function=code_imputation_functions.impute_age_category,
                   ws_code=CodeSchemes.WS_CORRECT_DATASET_SCHEME.get_code_with_match_value("age"),
                   raw_field_fold_strategy=FoldStrategies.assert_equal),

        CodingPlan(raw_field="recently_displaced_raw",
                   time_field="recently_displaced_time",
                   coda_filename="IMAQAL_recently_displaced.json",
                   coding_configurations=[
                       CodingConfiguration(
                           coding_mode=CodingModes.SINGLE,
                           code_scheme=CodeSchemes.RECENTLY_DISPLACED,
                           cleaner=somali.DemographicCleaner.clean_yes_no,
                           coded_field="recently_displaced_coded",
                           analysis_file_key="recently_displaced",
                           fold_strategy=FoldStrategies.assert_label_ids_equal,
                       )
                   ],
                   ws_code=CodeSchemes.WS_CORRECT_DATASET_SCHEME.get_code_with_match_value("recently displaced"),
                   raw_field_fold_strategy=FoldStrategies.assert_equal),

        CodingPlan(raw_field="household_language_raw",
                   time_field="household_language_time",
                   coda_filename="IMAQAL_household_language.json",
                   coding_configurations=[
                       CodingConfiguration(
                           coding_mode=CodingModes.SINGLE,
                           code_scheme=CodeSchemes.HOUSEHOLD_LANGUAGE,
                           coded_field="household_language_coded",
                           analysis_file_key="household_language",
                           fold_strategy=FoldStrategies.assert_label_ids_equal,
                       )
                   ],
                   ws_code=CodeSchemes.WS_CORRECT_DATASET_SCHEME.get_code_with_match_value("hh language"),
                   raw_field_fold_strategy=FoldStrategies.assert_equal),

        CodingPlan(raw_field="location_raw",
                   time_field="location_time",
                   coda_filename="IMAQAL_location.json",
                   coding_configurations=[
                       CodingConfiguration(
                           coding_mode=CodingModes.SINGLE,
                           code_scheme=CodeSchemes.MOGADISHU_SUB_DISTRICT,
                           fold_strategy=FoldStrategies.assert_label_ids_equal,
                           cleaner=somali.DemographicCleaner.clean_mogadishu_sub_district,
                           coded_field="mogadishu_sub_district_coded",
                           analysis_file_key="mogadishu_sub_district",
                           include_in_theme_distribution=False
                       ),
                       CodingConfiguration(
                           coding_mode=CodingModes.SINGLE,
                           code_scheme=CodeSchemes.SOMALIA_DISTRICT,
                           cleaner=lambda text: clean_district_if_no_mogadishu_sub_district(text),
                           fold_strategy=FoldStrategies.assert_label_ids_equal,
                           coded_field="district_coded",
                           analysis_file_key="district",
                           include_in_theme_distribution=False
                       ),
                       CodingConfiguration(
                           coding_mode=CodingModes.SINGLE,
                           code_scheme=CodeSchemes.SOMALIA_REGION,
                           fold_strategy=FoldStrategies.assert_label_ids_equal,
                           coded_field="region_coded",
                           analysis_file_key="region",
                       ),
                       CodingConfiguration(
                           coding_mode=CodingModes.SINGLE,
                           code_scheme=CodeSchemes.SOMALIA_STATE,
                           fold_strategy=FoldStrategies.assert_label_ids_equal,
                           coded_field="state_coded",
                           analysis_file_key="state",
                       ),
                       CodingConfiguration(
                           coding_mode=CodingModes.SINGLE,
                           code_scheme=CodeSchemes.SOMALIA_ZONE,
                           fold_strategy=FoldStrategies.assert_label_ids_equal,
                           coded_field="zone_coded",
                           analysis_file_key="zone",
                           include_in_theme_distribution=False
                       )
                   ],
                   code_imputation_function=code_imputation_functions.impute_somalia_location_codes,
                   ws_code=CodeSchemes.WS_CORRECT_DATASET_SCHEME.get_code_with_match_value("location"),
                   raw_field_fold_strategy=FoldStrategies.assert_equal)
    ]


def get_follow_up_coding_plans(pipeline_name):
    return []


def get_engagement_coding_plans(pipeline_name):
    return []


def get_ws_correct_dataset_scheme(pipeline_name):
    return CodeSchemes.WS_CORRECT_DATASET_SCHEME
