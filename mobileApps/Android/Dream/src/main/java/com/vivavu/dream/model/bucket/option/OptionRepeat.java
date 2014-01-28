package com.vivavu.dream.model.bucket.option;

import com.vivavu.dream.common.RepeatType;

/**
 * Created by yuja on 14. 1. 24.
 */
public class OptionRepeat {
    private RepeatType repeatType = RepeatType.WKRP;
    private boolean sun;
    private boolean mon;
    private boolean tue;
    private boolean wen;
    private boolean thu;
    private boolean fri;
    private boolean sat;

    private int repeatCount = 1;
    private int period;

    public OptionRepeat(){

    }

    public OptionRepeat(RepeatType repeatType, String optionStat) {
        this.repeatType = repeatType;
        setOptionStat(optionStat);
    }

    public RepeatType getRepeatType() {
        return repeatType;
    }

    public void setRepeatType(RepeatType repeatType) {
        this.repeatType = repeatType;
    }

    public boolean isSun() {
        return sun;
    }

    public void setSun(boolean sun) {
        this.sun = sun;
    }

    public boolean isMon() {
        return mon;
    }

    public void setMon(boolean mon) {
        this.mon = mon;
    }

    public boolean isTue() {
        return tue;
    }

    public void setTue(boolean tue) {
        this.tue = tue;
    }

    public boolean isWen() {
        return wen;
    }

    public void setWen(boolean wen) {
        this.wen = wen;
    }

    public boolean isThu() {
        return thu;
    }

    public void setThu(boolean thu) {
        this.thu = thu;
    }

    public boolean isFri() {
        return fri;
    }

    public void setFri(boolean fri) {
        this.fri = fri;
    }

    public boolean isSat() {
        return sat;
    }

    public void setSat(boolean sat) {
        this.sat = sat;
    }

    public int getRepeatCount() {
        return repeatCount;
    }

    public void setRepeatCount(int repeatCount) {
        this.repeatCount = repeatCount;
    }

    public int getPeriod() {
        return period;
    }

    public void setPeriod(int period) {
        this.period = period;
    }

    public String getOptionStat(){
        if(repeatType != RepeatType.NONE){
            StringBuffer sb = new StringBuffer();
            if(repeatType == RepeatType.WKRP){
                sb.append(mon?1:0).append(tue?1:0).append(wen?1:0).append(thu?1:0).append(fri?1:0).append(sat?1:0).append(sun?1:0);
            } else{
                sb.append(repeatCount);
            }

            return sb.toString();
        } else {
            return null;
        }
    }

    public void setOptionStat(String optionStat){
        if( optionStat != null && optionStat.length() == 7){
            repeatType = RepeatType.WKRP;
            mon = optionStat.substring(0, 1).equals("1");
            tue = optionStat.substring(1, 2).equals("1");
            wen = optionStat.substring(2, 3).equals("1");
            thu = optionStat.substring(3, 4).equals("1");
            fri = optionStat.substring(4, 5).equals("1");
            sat = optionStat.substring(5, 6).equals("1");
            sun = optionStat.substring(6, 7).equals("1");
        } else if(optionStat != null && optionStat.length() > 0 && optionStat.length() < 7){
            repeatCount = Integer.parseInt( optionStat);
        } else {
            mon=tue=wen=thu=fri=sat=sun=false;
        }
    }

    @Override
    public String toString() {
        return "OptionRepeat{" +
                "repeatType=" + repeatType +
                ", sun=" + sun +
                ", mon=" + mon +
                ", tue=" + tue +
                ", wen=" + wen +
                ", thu=" + thu +
                ", fri=" + fri +
                ", sat=" + sat +
                ", repeatCount=" + repeatCount +
                ", period=" + period +
                '}';
    }
}
