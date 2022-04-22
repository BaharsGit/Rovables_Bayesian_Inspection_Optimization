#ifndef RULES_SINGLETON_H_EXT_DET
#define RULES_SINGLETON_H_EXT_DET

#define LOOK_FOR_RULE_CHAIN_EXT() \
if (initial_state2 < initial_state1) {\
	combined_state = (initial_state2 << 16) | initial_state1;\
	swap = true;\
}\
else {\
	combined_state = (initial_state1 << 16) | initial_state2;\
}\
if(new_link) { \
	switch(combined_state) { \
	case 0x0 :\
		if (random_number < RAND_MAX) {\
			final_state1 = 0x1;\
			final_state2 = 0x2;\
			rule_type = 1; \
		}\
		break; \
	case 0x203 :\
		if (random_number < RAND_MAX) {\
			final_state1 = 0x3;\
			final_state2 = 0x4;\
			rule_type = 1; \
		}\
		break; \
	case 0x403 :\
		if (random_number < RAND_MAX) {\
			final_state1 = 0x5;\
			final_state2 = 0x6;\
			rule_type = 1; \
		}\
		break; \
	case 0x603 :\
		if (random_number < RAND_MAX) {\
			final_state1 = 0x7;\
			final_state2 = 0x8;\
			rule_type = 1; \
		}\
		break; \
	case 0x802 :\
		if (random_number < 0) {\
			final_state1 = 0xA;\
			final_state2 = 0x9;\
			rule_type = 1; \
		}\
		break; \
	default: \
		rule_type = 0; \
		break; \
	}; \
} \
else { \
	switch(combined_state) { \
	default: \
		rule_type = 0; \
		break; \
	}; \
	if (rule_type == 0) { \
		switch(combined_state) { \
	case 0x1000200 :\
		if (random_number < prob[0]) {\
			final_state1 = 0x0;\
			final_state2 = 0x0;\
			rule_type = 2; \
			ln_abs1 = 0xFF;\
			ln_abs2 = 0xFF;\
		}\
		break; \
	case 0x3000400 :\
		if (random_number < prob[1]) {\
			final_state1 = 0x0;\
			final_state2 = 0x2;\
			rule_type = 2; \
			ln_abs1 = (engaged_epm+1)%4;\
			ln_abs2 = 0xFF;\
		}\
		break; \
	case 0x5000600 :\
		if (random_number < prob[2]) {\
			final_state1 = 0x0;\
			final_state2 = 0x4;\
			rule_type = 2; \
			ln_abs1 = (engaged_epm+1)%4;\
			ln_abs2 = 0xFF;\
		}\
		break; \
	case 0x7000800 :\
		if (random_number < 0) {\
			final_state1 = 0x0;\
			final_state2 = 0x6;\
			rule_type = 2; \
			ln_abs1 = (engaged_epm+1)%4;\
			ln_abs2 = 0xFF;\
		}\
		break; \
	case 0x9000A00 :\
		if (random_number < 0) {\
			final_state1 = 0x0;\
			final_state2 = 0x8;\
			rule_type = 2; \
			ln_abs1 = (engaged_epm+2)%4;\
			ln_abs2 = 0xFF;\
		}\
		break; \
		default: \
			rule_type = 0; \
			break; \
		}; \
	}; \
}; 
#endif
