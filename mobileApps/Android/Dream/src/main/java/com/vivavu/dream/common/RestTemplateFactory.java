package com.vivavu.dream.common;

import com.vivavu.dream.model.user.User;

import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.http.converter.StringHttpMessageConverter;
import org.springframework.http.converter.json.MappingJacksonHttpMessageConverter;
import org.springframework.web.client.RestTemplate;

/**
 * Created by yuja on 14. 1. 8.
 */
public class RestTemplateFactory {
    private static RestTemplate restTemplate;
    private User user;

    public static RestTemplate getInstance(){
        if(restTemplate == null){
            restTemplate = new RestTemplate( new HttpComponentsClientHttpRequestFactory());
            restTemplate.getMessageConverters().add(new StringHttpMessageConverter());
            MappingJacksonHttpMessageConverter converter = new MappingJacksonHttpMessageConverter();
            //ObjectMapper om = converter.getObjectMapper();
            //om.configure(DeserializationConfig.Feature.UNWRAP_ROOT_VALUE, true);
            //om.configure(DeserializationConfig.Feature.FAIL_ON_UNKNOWN_PROPERTIES, false);//이부분은 json에 있는데 객체에 해당 대상이 없으면 그냥 넘기는 옵션

            restTemplate.getMessageConverters().add(converter);

        }
        return restTemplate;
    }

    public static RestTemplate getNewInstance(){
        RestTemplate newRestTemplate = new RestTemplate(new HttpComponentsClientHttpRequestFactory());
        newRestTemplate.getMessageConverters().add(new StringHttpMessageConverter());
        MappingJacksonHttpMessageConverter converter = new MappingJacksonHttpMessageConverter();
        newRestTemplate.getMessageConverters().add(converter);
        return newRestTemplate;
    }

}